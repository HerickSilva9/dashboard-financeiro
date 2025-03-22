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

# Testes para os novos indicadores de mercado
def test_yahoo_market_indicators():
    """Testa a rota /indicators/{ticker} com ticker válido"""
    response = client.get('/market/indicators/PETR4')
    assert response.status_code == 200
    data = response.json()
    
    verify_response_structure(data)
    assert data['success'] == True
    
    content = data['data']['content']
    assert isinstance(content, dict)
    
    # Verifica a estrutura dos dados fundamentalistas
    assert 'fundamentals' in content
    fundamentals = content['fundamentals']
    assert isinstance(fundamentals, dict)
    assert 'pe_ratio' in fundamentals
    assert 'pb_ratio' in fundamentals
    assert 'dividend_yield' in fundamentals
    assert 'roe' in fundamentals
    assert 'ebitda_margins' in fundamentals
    assert 'debt_to_equity' in fundamentals
    assert 'gross_margins' in fundamentals
    assert 'profit_margins' in fundamentals
    
    # Verifica a estrutura dos dados de mercado
    assert 'market_data' in content
    market_data = content['market_data']
    assert isinstance(market_data, dict)
    assert 'market_cap' in market_data
    assert 'average_volume' in market_data
    assert 'beta' in market_data
    assert 'fifty_two_week_high' in market_data
    assert 'fifty_two_week_low' in market_data
    assert 'short_ratio' in market_data
    assert 'regular_market_price' in market_data
    assert 'regular_market_volume' in market_data
    
    # Verifica a estrutura das informações de analistas
    assert 'analyst_info' in content
    analyst_info = content['analyst_info']
    assert isinstance(analyst_info, dict)
    assert 'target_mean_price' in analyst_info
    assert 'recommendation' in analyst_info
    assert 'number_of_analysts' in analyst_info
    assert 'earnings_growth' in analyst_info
    assert 'revenue_growth' in analyst_info
    assert 'recommendation_mean' in analyst_info

def test_yahoo_market_indicators_invalid_ticker():
    """Testa a rota /indicators/{ticker} com ticker inválido"""
    response = client.get('/market/indicators/XYZ123')
    assert response.status_code == 404
    data = response.json()
    
    verify_response_structure(data)
    assert data['success'] == False
    assert 'error' in data
    error = data['error']
    assert error['code'] == 'ASSET_NOT_FOUND'
    assert 'timestamp' in error['details']

def test_yahoo_market_indicators_partial_data():
    """Testa a rota /indicators/{ticker} com dados parciais"""
    response = client.get('/market/indicators/PETR4')
    assert response.status_code == 200
    data = response.json()
    
    verify_response_structure(data)
    assert data['success'] == True
    
    metadata = data['data'].get('metadata', {})
    
    # Se houver falha em alguma seção, verifica a estrutura dos metadados
    if 'failed_sections' in metadata:
        assert 'partial_data' in metadata
        assert metadata['partial_data'] == True
        assert isinstance(metadata['failed_sections'], list)
        
        content = data['data']['content']
        # Verifica se as seções que falharam estão como None
        for failed_section in metadata['failed_sections']:
            assert content[failed_section] is None

def test_yahoo_market_indicators_metadata():
    """Testa os metadados da resposta da rota /indicators/{ticker}"""
    response = client.get('/market/indicators/PETR4')
    assert response.status_code == 200
    data = response.json()
    
    verify_response_structure(data)
    assert data['success'] == True
    
    metadata = data['data'].get('metadata', {})
    assert 'provider' in metadata
    assert metadata['provider'] == 'yahoo'
    assert 'timezone' in metadata
    timezone = metadata['timezone']
    assert 'name' in timezone
    assert 'offset' in timezone
    assert 'is_dst' in timezone

def test_yahoo_market_indicators_all_sections_fail():
    """Testa o comportamento quando todas as seções falham"""
    # Este teste pode precisar de um mock para forçar todas as seções a falharem
    response = client.get('/market/indicators/INVALID')
    assert response.status_code in [404, 500]  # Pode ser 404 ou 500 dependendo do erro
    data = response.json()
    
    verify_response_structure(data)
    assert data['success'] == False
    assert 'error' in data
    error = data['error']
    
    if response.status_code == 500:
        assert error['code'] == 'INDICATORS_UNAVAILABLE'
        assert 'failed_sections' in error['details']
        assert len(error['details']['failed_sections']) == 3
    else:
        assert error['code'] == 'ASSET_NOT_FOUND' 