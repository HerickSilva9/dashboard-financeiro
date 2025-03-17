import os
from dotenv import load_dotenv

# Carregar variáveis do arquivo .env
load_dotenv()

# Definir configurações globais
BRAPI_TOKEN = os.getenv('BRAPI_TOKEN')
API_URL = os.getenv('API_URL', 'https://brapi.dev/api')