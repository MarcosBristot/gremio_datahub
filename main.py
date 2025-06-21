# main.py
import os
import requests
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta


load_dotenv()

app = FastAPI(
    title="Grêmio DataHub API",
    description="Uma API que centraliza notícias e estatísticas do Grêmio.",
    version="1.1.0" # Nova versão com busca inteligente
)

GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
APIFOOTBALL_API_KEY = os.getenv("APIFOOTBALL_API_KEY")
# =======================================================
#               CORREÇÃO DO ID DO TIME
# =======================================================
GREMIO_TEAM_ID = 130 
API_FOOTBALL_HOST = "v3.football.api-sports.io"
CURRENT_SEASON = 2023 # Definindo a temporada atual

def fetch_from_api(url, headers=None, params=None):
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail="Erro de comunicação com um serviço externo.")

@app.get("/")
def ler_raiz():
    return {"mensagem": "Bem-vindo ao Grêmio DataHub! O Imortal Tricolor em um só lugar."}

@app.get("/noticias")
def get_noticias():
    # ... (código da função de notícias, sem alterações)
    if not GNEWS_API_KEY:
        raise HTTPException(status_code=500, detail="A chave da API do GNews não foi configurada.")
    url = "https://gnews.io/api/v4/search"
    params = {"q": "Grêmio", "lang": "pt", "country": "br", "max": 10, "apikey": GNEWS_API_KEY}
    data = fetch_from_api(url, params=params)
    return {"noticias": data.get("articles", [])}

# =======================================================
#               LÓGICA DE BUSCA MELHORADA
# =======================================================
@app.get("/ultima-partida")
def get_ultima_partida():
    """
    Busca a última partida jogada na temporada, independentemente de quão longe ela esteja.
    """
    if not APIFOOTBALL_API_KEY:
        raise HTTPException(status_code=500, detail="A chave da API-Football não foi configurada.")
    
    url = f"https://{API_FOOTBALL_HOST}/fixtures"
    headers = {"x-rapidapi-host": API_FOOTBALL_HOST, "x-rapidapi-key": APIFOOTBALL_API_KEY}
    
    # Nova lógica: busca todos os jogos da temporada para o time
    params = {"team": GREMIO_TEAM_ID, "season": CURRENT_SEASON}
    
    data = fetch_from_api(url, headers=headers, params=params)
    
    if not data["response"]:
        return {"mensagem": f"Nenhuma partida encontrada para o Grêmio na temporada de {CURRENT_SEASON}."}

    # Filtra apenas as partidas que já terminaram ('Match Finished')
    partidas_finalizadas = [
        p for p in data["response"] 
        if p['fixture']['status']['short'] == 'FT'
    ]

    if not partidas_finalizadas:
        return {"mensagem": "Nenhuma partida finalizada encontrada ainda nesta temporada."}
        
    # Ordena as partidas pela data para garantir que a mais recente venha por último
    partidas_finalizadas.sort(key=lambda x: x['fixture']['timestamp'])
    
    # Pega a última partida da lista ordenada
    partida_info = partidas_finalizadas[-1]
    
    # Formata a resposta (código que já tínhamos)
    data_utc = datetime.fromtimestamp(partida_info['fixture']['timestamp'], tz=timezone.utc)
    data_local = data_utc.astimezone().strftime('%d/%m/%Y às %H:%M')

    return {
        "campeonato": partida_info['league']['name'], "rodada": partida_info['league']['round'],
        "data_hora": data_local, "estadio": partida_info['fixture']['venue']['name'],
        "status": partida_info['fixture']['status']['long'], "placar_casa": partida_info['goals']['home'],
        "time_casa": partida_info['teams']['home']['name'], "logo_casa": partida_info['teams']['home']['logo'],
        "placar_visitante": partida_info['goals']['away'], "time_visitante": partida_info['teams']['away']['name'],
        "logo_visitante": partida_info['teams']['away']['logo'],
    }


@app.get("/proxima-partida")
def get_proxima_partida():
    """
    Busca a próxima partida agendada, mesmo que esteja longe no futuro.
    """
    if not APIFOOTBALL_API_KEY:
        raise HTTPException(status_code=500, detail="A chave da API-Football não foi configurada.")
        
    url = f"https://{API_FOOTBALL_HOST}/fixtures"
    headers = {"x-rapidapi-host": API_FOOTBALL_HOST, "x-rapidapi-key": APIFOOTBALL_API_KEY}
    params = {"team": GREMIO_TEAM_ID, "season": CURRENT_SEASON}
    
    data = fetch_from_api(url, headers=headers, params=params)

    if not data["response"]:
        return {"mensagem": f"Nenhuma partida encontrada para o Grêmio na temporada de {CURRENT_SEASON}."}

    # Filtra apenas as partidas que ainda não aconteceram ('Not Started')
    partidas_agendadas = [
        p for p in data["response"] 
        if p['fixture']['status']['short'] == 'NS'
    ]
    
    if not partidas_agendadas:
        return {"mensagem": "Nenhuma próxima partida encontrada no calendário oficial desta temporada."}

    # Ordena pela data para pegar a mais próxima do futuro
    partidas_agendadas.sort(key=lambda x: x['fixture']['timestamp'])
    
    # Pega a primeira partida da lista ordenada
    partida_info = partidas_agendadas[0]
    
    data_utc = datetime.fromtimestamp(partida_info['fixture']['timestamp'], tz=timezone.utc)
    data_local = data_utc.astimezone().strftime('%d/%m/%Y às %H:%M')

    return {
        "campeonato": partida_info['league']['name'], "rodada": partida_info['league']['round'],
        "data_hora": data_local, "estadio": partida_info['fixture']['venue']['name'],
        "time_casa": partida_info['teams']['home']['name'], "logo_casa": partida_info['teams']['home']['logo'],
        "time_visitante": partida_info['teams']['away']['name'], "logo_visitante": partida_info['teams']['away']['logo'],
    }

@app.get("/dossie-ultima-partida")
def get_dossie_ultima_partida():
    if not APIFOOTBALL_API_KEY:
        raise HTTPException(status_code=500, detail="A chave da API-Football não foi configurada.")
    
    url_fixtures = f"https://{API_FOOTBALL_HOST}/fixtures"
    headers = {"x-rapidapi-host": API_FOOTBALL_HOST, "x-rapidapi-key": APIFOOTBALL_API_KEY}
    params = {"team": GREMIO_TEAM_ID, "season": CURRENT_SEASON}
    
    data_partidas = fetch_from_api(url_fixtures, headers=headers, params=params)
    
    if not data_partidas["response"]:
        return {"mensagem": f"Nenhuma partida encontrada para o Grêmio na temporada de {CURRENT_SEASON}."}
    
    partidas_finalizadas = [p for p in data_partidas["response"] if p['fixture']['status']['short'] == 'FT']
    if not partidas_finalizadas:
        return {"mensagem": f"Nenhuma partida finalizada encontrada na temporada {CURRENT_SEASON}."}
        
    partidas_finalizadas.sort(key=lambda x: x['fixture']['timestamp'])
    partida_info = partidas_finalizadas[-1]
    
    # ETAPA 2: Extrair informações e criar a janela de tempo
    adversario = partida_info['teams']['home']['name'] if "Grêmio" in partida_info['teams']['away']['name'] else partida_info['teams']['away']['name']
    
    match_timestamp = partida_info['fixture']['timestamp']
    match_date = datetime.fromtimestamp(match_timestamp, tz=timezone.utc)
    
    start_date = match_date - timedelta(days=1)
    end_date = match_date + timedelta(days=2)
    
    start_date_iso = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    end_date_iso = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')

    query_noticias = f'"Grêmio" E "{adversario}"'
    if not GNEWS_API_KEY:
        raise HTTPException(status_code=500, detail="A chave da API do GNews não foi configurada.")
    
    url_gnews = "https://gnews.io/api/v4/search"
    params_gnews = {
        "q": query_noticias,
        "lang": "pt",
        "country": "br",
        "max": 5,
        "from": start_date_iso, # <-- Filtro de data inicial
        "to": end_date_iso,     # <-- Filtro de data final
        "apikey": GNEWS_API_KEY
    }
    
    dados_noticias = fetch_from_api(url_gnews, params=params_gnews)
    
    dados_partida_formatado = get_ultima_partida() # Chamamos a função para formatar o JSON
    return {
        "partida": dados_partida_formatado,
        "noticias_relacionadas": dados_noticias.get("articles", [])
    }