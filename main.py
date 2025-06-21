# main.py
import os
import requests
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from datetime import datetime

# Carrega as variáveis do arquivo .env para o ambiente
load_dotenv()

# --- Configuração da Aplicação ---
app = FastAPI(
    title="Grêmio DataHub API",
    description="Uma API que centraliza notícias e estatísticas do Grêmio Foot-Ball Porto Alegrense.",
    version="0.2.0" # Subimos a versão!
)

# --- Chaves de API e Constantes ---
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
APIFOOTBALL_API_KEY = os.getenv("APIFOOTBALL_API_KEY")
GREMIO_TEAM_ID = 121
API_FOOTBALL_HOST = "v3.football.api-sports.io"


# --- Endpoints ---

@app.get("/")
def ler_raiz():
    """
    Endpoint de boas-vindas.
    """
    return {"mensagem": "Bem-vindo ao Grêmio DataHub! O Imortal Tricolor em um só lugar."}


@app.get("/noticias")
def get_noticias():
    """
    Busca as últimas notícias sobre o Grêmio na API do GNews.
    """
    if not GNEWS_API_KEY:
        raise HTTPException(status_code=500, detail="A chave da API do GNews não foi configurada.")

    url = "https://gnews.io/api/v4/search"
    params = {
        "q": "Grêmio", "lang": "pt", "country": "br", "max": 10, "apikey": GNEWS_API_KEY
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status() 
        data = response.json()
        return {"noticias": data.get("articles", [])}
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Erro ao contatar o serviço de notícias: {e}")


# NOVO ENDPOINT DE ESTATÍSTICAS!
@app.get("/proxima-partida")
def get_proxima_partida():
    """
    Busca informações da próxima partida oficial do Grêmio.
    """
    if not APIFOOTBALL_API_KEY:
        raise HTTPException(status_code=500, detail="A chave da API-Football não foi configurada.")

    url = f"https://{API_FOOTBALL_HOST}/fixtures"
    
    # A API-Football usa headers para autenticação, diferente do GNews
    headers = {
        "x-rapidapi-host": API_FOOTBALL_HOST,
        "x-rapidapi-key": APIFOOTBALL_API_KEY
    }
    # Parâmetros para buscar o próximo 1 jogo do time
    params = {
        "team": GREMIO_TEAM_ID,
        "next": 1,
        "timezone": "America/Sao_Paulo" # Fuso horário importante para a data/hora corretas
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Verifica se a API retornou alguma partida
        if not data["response"]:
            return {"mensagem": "Nenhuma próxima partida encontrada no calendário oficial."}
        
        # Extrai e formata as informações mais importantes da partida
        partida_info = data["response"][0]
        
        # Converte a data para um formato mais legível
        data_utc = datetime.fromisoformat(partida_info['fixture']['date'])
        data_local = data_utc.strftime('%d/%m/%Y às %H:%M') # Formato Dia/Mês/Ano às Hora:Minuto

        return {
            "campeonato": partida_info['league']['name'],
            "rodada": partida_info['league']['round'],
            "data_hora": data_local,
            "estadio": partida_info['fixture']['venue']['name'],
            "time_casa": partida_info['teams']['home']['name'],
            "logo_casa": partida_info['teams']['home']['logo'],
            "time_visitante": partida_info['teams']['away']['name'],
            "logo_visitante": partida_info['teams']['away']['logo'],
        }

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Erro ao contatar o serviço de estatísticas: {e}")