from fastapi.testclient import TestClient
import sys
import os
from backend.main import app  # Importa a API do arquivo principal

client = TestClient(app)

# Teste para a rota raiz (/)
def test_read_root():
    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {"message": "API está rodando!"}
    # Verifica se a rota raiz retorna a mensagem esperada (ajuste conforme sua implementação)

# Teste para /available_assets
def test_available_assets():
    response = client.get('/available_assets')
    assert response.status_code == 200
    data = response.json()
    assert 'stocks' in data  # Verifica se a chave 'stocks' está presente
    assert isinstance(data['stocks'], list)  # Verifica se 'stocks' é uma lista

# Teste para /available_assets com parâmetro de busca
def test_available_assets_with_search():
    response = client.get('/available_assets?search=MGLU3')
    assert response.status_code == 200
    data = response.json()
    assert 'stocks' in data
    assert isinstance(data['stocks'], list)
    assert len(data['stocks']) > 0
    assert 'MGLU3' in data['stocks']  # Verifica se 'MGLU3' está na lista de strings
    
# Teste para /quote/{ticker} com parâmetros válidos
def test_ticker_quote():
    response = client.get('/quote/MGLU3.SA?range=1mo&interval=1d')
    assert response.status_code == 200
    data = response.json()
    assert 'results' in data  # Verifica se a chave 'results' existe
    assert isinstance(data['results'], list)
    assert len(data['results']) > 0
    assert 'symbol' in data['results'][0]  # Verifica se os dados têm a chave 'symbol'
    assert data['results'][0]['symbol'] == 'MGLU3.SA'  # Verifica o ticker retornado

# Teste para /quote/{ticker} com ticker inválido
def test_ticker_quote_invalid():
    response = client.get('/quote/XYZ123?range=1mo&interval=1d')
    assert response.status_code == 404  # Ajustado para esperar 404
    data = response.json()
    assert 'detail' in data  # Verifica a chave 'detail' em vez de 'error'
    assert data['detail'] == 'No data available'  # Verifica o valor de 'detail'

# Teste para /quote/{ticker} com diferentes parâmetros
def test_ticker_quote_different_range():
    response = client.get('/quote/MGLU3.SA?range=5d&interval=1d')
    assert response.status_code == 200
    data = response.json()
    assert 'results' in data

# Teste para /quote_list com parâmetros válidos
def test_quote_list():
    response = client.get('/quote_list?search=TR&sortBy=close&sortOrder=desc&limit=10&sector=finance')
    assert response.status_code == 200
    data = response.json()
    assert 'stocks' in data
    assert isinstance(data['stocks'], list)
    assert len(data['stocks']) <= 10  # Verifica se o limite é respeitado

# Teste para /quote_list com busca inválida
def test_quote_list_invalid():
    response = client.get('/quote_list?search=INVALIDO&sortBy=close&sortOrder=desc&limit=10&sector=finance')
    assert response.status_code == 200
    data = response.json()
    assert 'error' in data
    assert data['error'] == 'No data available'  # Ajuste conforme a mensagem real da sua API

# Teste para /quote_list com limite diferente
def test_quote_list_with_limit():
    response = client.get('/quote_list?limit=5')
    assert response.status_code == 200
    data = response.json()
    assert 'stocks' in data
    assert len(data['stocks']) == 5  # Verifica se o limite é aplicado corretamente