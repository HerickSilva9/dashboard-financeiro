import pytest
from fastapi.testclient import TestClient
import sys
import os
from backend.main import app
from backend.services.provider_manager import ProviderManager
from backend.providers.yahoo_provider import YahooProvider
from dotenv import load_dotenv

# Configuração do cliente de teste da API
client = TestClient(app)

def test_env_file_exists():
    """Testa se o arquivo .env existe e contém as variáveis necessárias."""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    
    # Verifica se o arquivo existe
    assert os.path.exists(env_path), "Arquivo .env não encontrado"
    
    # Carrega as variáveis do arquivo
    load_dotenv(env_path)

# Testes do ProviderManager com Yahoo Finance
@pytest.mark.asyncio
async def test_provider_manager_yahoo_initialization():
    manager = ProviderManager()
    assert 'yahoo' in manager._providers
    assert manager._default_providers['get_historical_prices'] == 'yahoo'
    assert manager._default_providers['get_available_assets'] == 'brapi'

@pytest.mark.asyncio
async def test_provider_manager_yahoo_get_provider():
    manager = ProviderManager()
    # Testa provedor padrão para get_historical_prices
    async with manager.get_provider(route_name='get_historical_prices') as provider:
        assert isinstance(provider, YahooProvider)

# Teste para /available_assets com Yahoo Finance
def test_yahoo_available_assets():
    response = client.get('/market/assets')
    assert response.status_code == 200
    data = response.json()
    assert data['success'] == True
    assert 'data' in data
    assert isinstance(data['data'], dict)
    assert 'stocks' in data['data']
    assert 'indexes' in data['data']
    assert isinstance(data['data']['stocks'], list)
    assert isinstance(data['data']['indexes'], list)

# Teste para /quote/{ticker} com Yahoo Finance (provedor padrão)
def test_yahoo_ticker_quote():
    response = client.get('/market/prices/PETR4?range=5d&interval=1d')
    assert response.status_code == 200
    data = response.json()
    assert data['success'] == True
    assert 'data' in data
    assert isinstance(data['data'], dict)
    assert 'symbol' in data['data']
    assert 'name' in data['data']
    assert 'currency' in data['data']
    assert 'prices' in data['data']
    assert isinstance(data['data']['prices'], list)
    assert len(data['data']['prices']) > 0

# Teste para /quote/{ticker} com ticker inválido no Yahoo Finance
def test_yahoo_ticker_quote_invalid():
    response = client.get('/market/prices/XYZ123?range=5d&interval=1d')
    assert response.status_code == 404
    data = response.json()
    assert data['success'] == False
    assert 'error' in data
    error = data['error']
    assert error['code'] == 'PROVIDER_ERROR'

# Teste para /quote/{ticker} com diferentes intervalos no Yahoo Finance
def test_yahoo_ticker_quote_different_intervals():
    intervals = ['1d', '1wk', '1mo']
    for interval in intervals:
        response = client.get(f'/market/prices/PETR4?range=1mo&interval={interval}')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] == True
        assert 'data' in data
        assert isinstance(data['data'], dict)
        assert 'symbol' in data['data']
        assert 'name' in data['data']
        assert 'currency' in data['data']
        assert 'prices' in data['data']
        assert isinstance(data['data']['prices'], list)
        assert len(data['data']['prices']) > 0

# Teste para /quote/{ticker} com diferentes ranges no Yahoo Finance
def test_yahoo_ticker_quote_different_ranges():
    ranges = ['1d', '5d', '1mo', '3mo', '6mo', '1y']
    for range_value in ranges:
        response = client.get(f'/market/prices/PETR4?range={range_value}&interval=1d')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] == True
        assert 'data' in data
        assert isinstance(data['data'], dict)
        assert 'symbol' in data['data']
        assert 'name' in data['data']
        assert 'currency' in data['data']
        assert 'prices' in data['data']
        assert isinstance(data['data']['prices'], list)
        assert len(data['data']['prices']) > 0

# Teste para verificar se o sufixo .SA é adicionado corretamente
def test_yahoo_ticker_suffix():
    response = client.get('/market/prices/PETR4?range=1d&interval=1d')
    assert response.status_code == 200
    data = response.json()
    assert data['success'] == True
    assert data['data']['symbol'] == 'PETR4.SA'

# Teste para verificar se o sufixo .SA não é duplicado
def test_yahoo_ticker_suffix_no_duplicate():
    response = client.get('/market/prices/PETR4.SA?range=1d&interval=1d')
    assert response.status_code == 200
    data = response.json()
    assert data['success'] == True
    assert data['data']['symbol'] == 'PETR4.SA' 