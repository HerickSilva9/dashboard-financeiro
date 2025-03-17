#################
# routes/quotes.py
#################

from fastapi import APIRouter
from backend.services.brapi_service import BrapiService

# Cria um roteador para agrupar as rotas relacionadas a cotações
router = APIRouter()

@router.get('/available_assets')
def get_available_assets(search: str = ''):
    service = BrapiService()
    return service.get_available_assets(search)

@router.get('/quote/{ticker}')
def get_ticker_quote(ticker: str, range: str = '1d', interval: str = '', fundamental: str = 'false', dividends: str = 'false', modules: str = ''):
    service = BrapiService()
    return service.get_ticker_quote(ticker, range, interval, fundamental, dividends, modules)

@router.get('/quote_list')
def get_quote_list(search: str = '', sortBy: str = '', sortOrder: str = '', limit: int = 10, sector: str = ''):
    service = BrapiService()
    return service.get_quote_list(search, sortBy, sortOrder, limit, sector)