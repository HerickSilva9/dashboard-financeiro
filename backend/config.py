import os
from dotenv import load_dotenv

# Carregar variáveis do arquivo .env
load_dotenv()

# Configurações da API BrAPI
BRAPI_TOKEN = os.getenv('BRAPI_TOKEN', '')
API_URL = os.getenv('API_URL', 'https://brapi.dev/api')

# Configurações gerais da aplicação
DEFAULT_PROVIDER = os.getenv('DEFAULT_PROVIDER', 'brapi')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'ERROR')