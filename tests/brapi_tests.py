import pytest
from fastapi.testclient import TestClient
import sys
import os
from backend.main import app  # Importa a API do arquivo principal
from backend.services.provider_manager import ProviderManager
from backend.providers.brapi_provider import BrapiProvider
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
    
    # Verifica se as variáveis necessárias estão definidas
    assert os.getenv('BRAPI_TOKEN'), "BRAPI_TOKEN não está definido no arquivo .env"
    assert os.getenv('API_URL'), "API_URL não está definido no arquivo .env"
    assert os.getenv('DEFAULT_PROVIDER'), "DEFAULT_PROVIDER não está definido no arquivo .env"
    
    # Verifica se o token não está vazio
    assert os.getenv('BRAPI_TOKEN') != '', "BRAPI_TOKEN está vazio no arquivo .env"
    
    # Verifica se a URL da API está correta
    assert os.getenv('API_URL') == 'https://brapi.dev/api', "API_URL está incorreta no arquivo .env"

# Testes do ProviderManager
@pytest.mark.asyncio
async def test_provider_manager_initialization():
    manager = ProviderManager()
    assert 'brapi' in manager._providers
    assert manager._default_provider == 'brapi'

@pytest.mark.asyncio
async def test_provider_manager_registration():
    manager = ProviderManager()
    # Testa registro de um novo provedor
    manager.register_provider('test_provider', BrapiProvider)
    assert 'test_provider' in manager._providers

@pytest.mark.asyncio
async def test_provider_manager_set_default():
    manager = ProviderManager()
    manager.register_provider('test_provider', BrapiProvider)
    manager.set_default_provider('test_provider')
    assert manager._default_provider == 'test_provider'

@pytest.mark.asyncio
async def test_provider_manager_get_provider():
    manager = ProviderManager()
    async with manager.get_provider() as provider:
        assert isinstance(provider, BrapiProvider)

@pytest.mark.asyncio
async def test_provider_manager_invalid_provider():
    manager = ProviderManager()
    with pytest.raises(ValueError):
        async with manager.get_provider('invalid_provider') as _:
            pass

# Teste para a rota raiz (/)
def test_read_root():
    response = client.get('/')
    assert response.status_code == 200
    data = response.json()
    assert data['success'] == True
    assert data['data']['message'] == "API de dados de mercado financeiro está operacional!"

# Teste para /available_assets
def test_available_assets():
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

# Teste para /available_assets com parâmetro de busca
def test_available_assets_with_search():
    response = client.get('/market/assets?search=MGLU3')
    assert response.status_code == 200
    data = response.json()
    assert data['success'] == True
    assert 'data' in data
    assert isinstance(data['data'], dict)
    assert 'stocks' in data['data']
    assert 'indexes' in data['data']
    assert isinstance(data['data']['stocks'], list)
    assert isinstance(data['data']['indexes'], list)
    assert len(data['data']['stocks']) > 0
    assert 'MGLU3' in data['data']['stocks']
    
# Teste para /quote/{ticker} com parâmetros válidos
def test_ticker_quote():
    response = client.get('/market/prices/MGLU3?range=5d&interval=1d')
    assert response.status_code == 200
    data = response.json()
    assert data['success'] == True
    assert 'data' in data
    assert isinstance(data['data'], dict)
    assert 'results' in data['data']
    assert isinstance(data['data']['results'], list)
    assert len(data['data']['results']) > 0
    result = data['data']['results'][0]
    assert 'symbol' in result
    assert 'historicalDataPrice' in result
    assert isinstance(result['historicalDataPrice'], list)
    assert result['symbol'] == 'MGLU3'
    assert len(result['historicalDataPrice']) > 0
    assert all(key in result['historicalDataPrice'][0] for key in ['date', 'open', 'high', 'low', 'close', 'volume'])

# Teste para /quote/{ticker} com ticker inválido
def test_ticker_quote_invalid():
    response = client.get('/market/prices/XYZ123?range=5d&interval=1d')
    assert response.status_code == 404
    data = response.json()
    assert data['success'] == False
    assert 'error' in data
    error = data['error']
    assert error['code'] == 'NO_DATA_AVAILABLE'
    assert 'Nenhum dado disponível' in error['message']
    assert 'ticker' in error['details']

# Teste para /quote/{ticker} com diferentes parâmetros
def test_ticker_quote_different_range():
    response = client.get('/market/prices/MGLU3?range=1mo&interval=1d')
    assert response.status_code == 200
    data = response.json()
    assert data['success'] == True
    assert 'data' in data
    assert isinstance(data['data'], dict)
    assert 'results' in data['data']
    assert isinstance(data['data']['results'], list)
    if len(data['data']['results']) > 0:
        result = data['data']['results'][0]
        assert 'historicalDataPrice' in result
        assert isinstance(result['historicalDataPrice'], list)
        assert len(result['historicalDataPrice']) > 0
        assert all(key in result['historicalDataPrice'][0] for key in ['date', 'open', 'high', 'low', 'close', 'volume'])

# Teste para /quote_list com parâmetros válidos
def test_quote_list():
    response = client.get('/market/assets?search=TR&provider=brapi')
    assert response.status_code == 200
    data = response.json()
    assert data['success'] == True
    assert 'data' in data
    assert isinstance(data['data'], dict)
    assert 'stocks' in data['data']
    assert 'indexes' in data['data']
    assert isinstance(data['data']['stocks'], list)
    assert isinstance(data['data']['indexes'], list)
    assert len(data['data']['stocks']) > 0

# Teste para /quote_list com busca inválida
def test_quote_list_invalid():
    response = client.get('/market/assets?search=INVALIDO&provider=brapi')
    assert response.status_code == 200
    data = response.json()
    assert data['success'] == True
    assert 'data' in data
    assert isinstance(data['data'], dict)
    assert 'stocks' in data['data']
    assert 'indexes' in data['data']
    assert isinstance(data['data']['stocks'], list)
    assert isinstance(data['data']['indexes'], list)
    assert len(data['data']['stocks']) == 0

# Teste para /quote_list com limite diferente
def test_quote_list_with_limit():
    response = client.get('/market/assets?provider=brapi')
    assert response.status_code == 200
    data = response.json()
    assert data['success'] == True
    assert 'data' in data
    assert isinstance(data['data'], dict)
    assert 'stocks' in data['data']
    assert 'indexes' in data['data']
    assert isinstance(data['data']['stocks'], list)
    assert isinstance(data['data']['indexes'], list)