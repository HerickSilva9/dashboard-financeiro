import pytest
from fastapi.testclient import TestClient
import sys
import os
from datetime import datetime
from backend.main import app
from backend.services.provider_manager import ProviderManager
from backend.providers.yahoo_provider import YahooProvider
from dotenv import load_dotenv

# Configuração do cliente de teste da API
client = TestClient(app)

def verify_response_structure(data):
    """Função auxiliar para verificar a estrutura padrão da resposta"""
    assert 'success' in data
    assert 'data' in data
    
    if data['success']:
        assert data['data'] is not None
        assert 'timestamp' in data['data']
        assert 'content' in data['data']
        try:
            datetime.fromisoformat(data['data']['timestamp'])
        except ValueError:
            pytest.fail("Timestamp não está em formato ISO")
    else:
        assert 'error' in data
        assert data['error'] is not None
        assert 'code' in data['error']
        assert 'message' in data['error']
        assert 'details' in data['error']
        assert 'timestamp' in data['error']['details']
        try:
            datetime.fromisoformat(data['error']['details']['timestamp'])
        except ValueError:
            pytest.fail("Timestamp do erro não está em formato ISO")

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

@pytest.mark.asyncio
async def test_provider_manager_yahoo_get_provider():
    manager = ProviderManager()
    async with manager.get_provider(route_name='get_historical_prices') as provider:
        assert isinstance(provider, YahooProvider)

# Teste para /quote/{ticker} com ticker válido
def test_yahoo_ticker_quote():
    """Testa a rota /prices/{ticker} com ticker válido"""
    response = client.get('/market/prices/PETR4?range=5d&interval=1d')
    assert response.status_code == 200
    data = response.json()
    
    verify_response_structure(data)
    assert data['success'] == True
    
    content = data['data']['content']
    assert isinstance(content, dict)
    assert 'symbol' in content
    assert 'name' in content
    assert 'currency' in content
    assert 'prices' in content
    assert isinstance(content['prices'], list)
    assert len(content['prices']) > 0

# Teste para /quote/{ticker} com ticker inválido
def test_yahoo_ticker_quote_invalid():
    """Testa a rota /prices/{ticker} com ticker inválido"""
    response = client.get('/market/prices/XYZ123?range=5d&interval=1d')
    assert response.status_code == 404
    data = response.json()
    
    verify_response_structure(data)
    assert data['success'] == False
    assert 'error' in data
    error = data['error']
    assert error['code'] == 'ASSET_NOT_FOUND'
    assert 'timestamp' in error['details']

# Teste para /quote/{ticker} com diferentes intervalos
def test_yahoo_ticker_quote_different_intervals():
    """Testa a rota /prices/{ticker} com diferentes intervalos"""
    response = client.get('/market/prices/PETR4?range=5d&interval=1h')
    assert response.status_code == 200
    data = response.json()
    
    verify_response_structure(data)
    assert data['success'] == True
    
    content = data['data']['content']
    assert isinstance(content, dict)
    assert 'symbol' in content
    assert 'name' in content
    assert 'currency' in content
    assert 'prices' in content
    assert isinstance(content['prices'], list)
    assert len(content['prices']) > 0

# Teste para /quote/{ticker} com diferentes ranges
def test_yahoo_ticker_quote_different_ranges():
    """Testa a rota /prices/{ticker} com diferentes ranges"""
    response = client.get('/market/prices/PETR4?range=1mo&interval=1d')
    assert response.status_code == 200
    data = response.json()
    
    verify_response_structure(data)
    assert data['success'] == True
    
    content = data['data']['content']
    assert isinstance(content, dict)
    assert 'symbol' in content
    assert 'name' in content
    assert 'currency' in content
    assert 'prices' in content
    assert isinstance(content['prices'], list)
    assert len(content['prices']) > 0

# Teste para verificar se o sufixo .SA é adicionado corretamente
def test_yahoo_ticker_suffix():
    """Testa se o sufixo .SA é adicionado corretamente"""
    response = client.get('/market/prices/PETR4?range=5d&interval=1d')
    assert response.status_code == 200
    data = response.json()
    
    verify_response_structure(data)
    assert data['success'] == True
    
    content = data['data']['content']
    assert content['symbol'] == 'PETR4.SA'

# Teste para verificar se o sufixo .SA não é duplicado
def test_yahoo_ticker_suffix_no_duplicate():
    """Testa se não há duplicação do sufixo .SA"""
    response = client.get('/market/prices/PETR4.SA?range=5d&interval=1d')
    assert response.status_code == 200
    data = response.json()
    
    verify_response_structure(data)
    assert data['success'] == True
    
    content = data['data']['content']
    assert content['symbol'] == 'PETR4.SA' 