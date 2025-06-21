from fastapi import FastAPI

# Cria uma "instância" da aplicação FastAPI
# Esta variável 'app' é a referência principal para toda a nossa API.
app = FastAPI(
    title="Grêmio DataHub API",
    description="Uma API que centraliza notícias e estatísticas do Grêmio Foot-Ball Porto Alegrense.",
    version="0.1.0"
)

# Este é um "decorator" do FastAPI.
# Ele diz ao FastAPI que a função logo abaixo é responsável por
# lidar com as requisições que chegam via GET para a URL raiz ("/").
@app.get("/")
def ler_raiz():
    """
    Endpoint de boas-vindas. Retorna uma mensagem inicial.
    """
    return {"mensagem": "Bem-vindo ao Grêmio DataHub! O Imortal Tricolor em um só lugar."}