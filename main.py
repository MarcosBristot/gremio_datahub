# main.py
import os
import requests
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = FastAPI(
    title="Grêmio DataHub API",
    description="Uma API que centraliza notícias e estatísticas do Grêmio.",
    version="1.0.0" # Versão 1.0! Projeto completo!
)

GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
APIFOOTBALL_API_KEY = os.getenv("APIFOOTBALL_API_KEY")
GREMIO_TEAM_ID = 130
API_FOOTBALL_HOST = "v3.football.api-sports.io"

# --- Funções Auxiliares (Refatorando para não repetir código) ---

def fetch_from_api(url, headers=None, params=None):
    """Função genérica para fazer requisições e tratar erros comuns."""
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # Para o usuário final, o detalhe técnico do erro não é tão importante.
        raise HTTPException(status_code=503, detail="Erro de comunicação com um serviço externo.")


# --- Endpoints ---

@app.get("/")
def ler_raiz():
    return {"mensagem": "Bem-vindo ao Grêmio DataHub! O Imortal Tricolor em um só lugar."}

@app.get("/noticias")
def get_noticias():
    if not GNEWS_API_KEY:
        raise HTTPException(status_code=500, detail="A chave da API do GNews não foi configurada.")
    url = "https://gnews.io/api/v4/search"
    params = {"q": "Grêmio", "lang": "pt", "country": "br", "max": 10, "apikey": GNEWS_API_KEY}
    data = fetch_from_api(url, params=params)
    return {"noticias": data.get("articles", [])}

@app.get("/ultima-partida")
def get_ultima_partida():
    if not APIFOOTBALL_API_KEY:
        raise HTTPException(status_code=500, detail="A chave da API-Football não foi configurada.")
    url = f"https://{API_FOOTBALL_HOST}/fixtures"
    headers = {"x-rapidapi-host": API_FOOTBALL_HOST, "x-rapidapi-key": APIFOOTBALL_API_KEY}
    params = {"team": GREMIO_TEAM_ID, "last": 1, "timezone": "America/Sao_Paulo"}
    data = fetch_from_api(url, headers=headers, params=params)
    if not data["response"]:
        return {"mensagem": "Nenhuma última partida foi encontrada nos registros."}
    partida_info = data["response"][0]
    data_utc = datetime.fromisoformat(partida_info['fixture']['date'])
    data_local = data_utc.strftime('%d/%m/%Y às %H:%M')
    return {
        "campeonato": partida_info['league']['name'], "rodada": partida_info['league']['round'],
        "data_hora": data_local, "estadio": partida_info['fixture']['venue']['name'],
        "status": partida_info['fixture']['status']['long'], "placar_casa": partida_info['goals']['home'],
        "time_casa": partida_info['teams']['home']['name'], "logo_casa": partida_info['teams']['home']['logo'],
        "placar_visitante": partida_info['goals']['away'], "time_visitante": partida_info['teams']['away']['name'],
        "logo_visitante": partida_info['teams']['away']['logo'],
    }


@app.get("/dossie-ultima-partida")
def get_dossie_ultima_partida():
    """
    Busca os dados da última partida e as notícias relacionadas a ela.
    """
    dados_partida = get_ultima_partida()
    
    if "mensagem" in dados_partida:
        return dados_partida

    adversario = ""
    if "Grêmio" in dados_partida["time_casa"]:
        adversario = dados_partida["time_visitante"]
    else:
        adversario = dados_partida["time_casa"]
    
    # ETAPA 3: Buscar as notícias com a query específica
    query_noticias = f'"Grêmio" E "{adversario}"'
    
    if not GNEWS_API_KEY:
        raise HTTPException(status_code=500, detail="A chave da API do GNews não foi configurada.")
    
    url_gnews = "https://gnews.io/api/v4/search"
    params_gnews = {"q": query_noticias, "lang": "pt", "country": "br", "max": 5, "apikey": GNEWS_API_KEY}
    
    dados_noticias = fetch_from_api(url_gnews, params=params_gnews)
    
    return {
        "partida": dados_partida,
        "noticias_relacionadas": dados_noticias.get("articles", [])
    }