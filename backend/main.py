from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
import os

from backend.routes.market_routes import router as market_router
from backend.config import DEBUG, LOG_LEVEL
from backend.services.provider_manager import provider_manager
from backend.models import APIResponse
from backend.utils.response import ResponseUtil

# Caminho relativo ao diretório de main.py
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)  # Cria a pasta logs se não existir
log_file = os.path.join(log_dir, 'app.log')

# Configuração do logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Inicialização do FastAPI
app = FastAPI(
    title="Market Data API",
    description="API para acesso a dados de mercado financeiro",
    version="1.0.0",
    debug=DEBUG
)

# Configuração do CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Defina as origens permitidas em ambiente de produção
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Inclui as rotas de mercado
app.include_router(market_router)

# Rota raiz
@app.get("/", response_model=APIResponse)
async def read_root():
    """Rota raiz para verificar se a API está funcionando."""
    return ResponseUtil.success(
        message="API de dados de mercado financeiro está operacional!",
        metadata={
            "version": "1.0.0",
            "environment": "development" if DEBUG else "production"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)