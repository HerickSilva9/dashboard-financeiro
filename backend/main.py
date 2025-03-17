#################
# main.py
#################

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
import os
from backend.routes import stock_quotes  # Importa as rotas de quotes.py

# Caminho relativo ao diretório de main.py
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)  # Cria a pasta logs se não existir
log_file = os.path.join(log_dir, 'app.log')

# Configuração do logging
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),  # Salva em app/logs/app.log
        logging.StreamHandler(sys.stdout)
    ]
)

# Inicialização do FastAPI
app = FastAPI()

# Configuração do CORS (ajuste as origens permitidas quando o frontend estiver pronto)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # '*' para permitir todas as origens por enquanto
    allow_credentials=True,
    allow_methods=['GET'],
    allow_headers=['*'],
)

# Inclui as rotas definidas em quotes.py
app.include_router(stock_quotes.router)

# Rota raiz para verificar se a API está rodando
@app.get("/")
def read_root():
    return {"message": "API está rodando!"}