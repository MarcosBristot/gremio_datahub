# teste_api.py
import os
import requests
from dotenv import load_dotenv
import json # Biblioteca para formatar a saída e facilitar a leitura

print("--- Iniciando teste de diagnóstico direto na API-Football ---")

load_dotenv()
API_KEY = os.getenv("APIFOOTBALL_API_KEY")

# Vamos testar com os parâmetros que deveriam funcionar
TEAM_ID = 130
SEASON = 2024

if not API_KEY:
    print("\nERRO CRÍTICO: Não foi possível encontrar a APIFOOTBALL_API_KEY no arquivo .env.")
else:
    print(f"\nTentando buscar dados para Time ID: {TEAM_ID}, Temporada: {SEASON}")
    
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {
        "x-rapidapi-host": "v3.football.api-sports.io",
        "x-rapidapi-key": API_KEY
    }
    params = {"team": TEAM_ID, "season": SEASON}

    try:
        response = requests.get(url, headers=headers, params=params)
        
        print(f"\nStatus Code da Resposta: {response.status_code}")
        
        response_data = response.json()
        
        print("\n--- RESPOSTA BRUTA DA API ---")
        # Usamos json.dumps para imprimir o JSON de forma organizada (identada)
        print(json.dumps(response_data, indent=2))

    except requests.exceptions.RequestException as e:
        print(f"\nERRO DE CONEXÃO: {e}")