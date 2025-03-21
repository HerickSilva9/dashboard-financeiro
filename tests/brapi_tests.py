import pytest
from fastapi.testclient import TestClient
import sys
import os
from datetime import datetime
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
    
    # Verifica se o token não está vazio
    assert os.getenv('BRAPI_TOKEN') != '', "BRAPI_TOKEN está vazio no arquivo .env"
    
    # Verifica se a URL da API está correta
    assert os.getenv('API_URL') == 'https://brapi.dev/api', "API_URL está incorreta no arquivo .env"

# Testes do ProviderManager
@pytest.mark.asyncio
async def test_provider_manager_initialization():
    manager = ProviderManager()
    assert 'brapi' in manager._providers
    assert manager._default_providers['get_available_assets'] == 'brapi'

@pytest.mark.asyncio
async def test_provider_manager_registration():
    manager = ProviderManager()
    # Testa registro de um novo provedor
    manager.register_provider('test_provider', BrapiProvider)
    assert 'test_provider' in manager._providers

@pytest.mark.asyncio
async def test_provider_manager_set_default_for_route():
    manager = ProviderManager()
    # Registra um novo provedor
    manager.register_provider('test_provider', BrapiProvider)
    # Testa definição de provedor padrão para uma rota
    manager.set_default_provider_for_route('get_available_assets', 'test_provider')
    assert manager._default_providers['get_available_assets'] == 'test_provider'

@pytest.mark.asyncio
async def test_provider_manager_get_provider():
    manager = ProviderManager()
    # Testa provedor padrão para get_available_assets
    async with manager.get_provider(route_name='get_available_assets') as provider:
        assert isinstance(provider, BrapiProvider)

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

# Teste para /available_assets (provedor padrão: brapi)
def test_brapi_available_assets():
    """Testa a rota /available_assets com o provedor Brapi"""
    response = client.get('/market/assets')
    assert response.status_code == 200
    data = response.json()
    
    verify_response_structure(data)
    assert data['success'] == True
    
    content = data['data']['content']
    assert isinstance(content, dict)
    assert 'stocks' in content
    assert 'indexes' in content
    assert isinstance(content['stocks'], list)
    assert isinstance(content['indexes'], list)

# Teste para /available_assets com termo de busca
def test_brapi_available_assets_with_search():
    """Testa a rota /available_assets com termo de busca usando o provedor Brapi"""
    response = client.get('/market/assets?search=PETR')
    assert response.status_code == 200
    data = response.json()
    
    verify_response_structure(data)
    assert data['success'] == True
    
    content = data['data']['content']
    assert isinstance(content, dict)
    assert 'stocks' in content
    assert 'indexes' in content
    assert isinstance(content['stocks'], list)
    assert isinstance(content['indexes'], list)
    assert any('PETR' in stock for stock in content['stocks'])

# Teste para /available_assets com termo de busca inválido
def test_brapi_available_assets_invalid_search():
    """Testa a rota /available_assets com termo de busca inválido usando o provedor Brapi"""
    response = client.get('/market/assets?search=XYZ123')
    assert response.status_code == 200
    data = response.json()
    
    verify_response_structure(data)
    assert data['success'] == True
    
    content = data['data']['content']
    assert isinstance(content, dict)
    assert 'stocks' in content
    assert 'indexes' in content
    assert isinstance(content['stocks'], list)
    assert isinstance(content['indexes'], list)
    assert len(content['stocks']) == 0
    assert len(content['indexes']) == 0