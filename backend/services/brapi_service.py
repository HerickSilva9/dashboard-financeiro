#################
# services/brapi_service.py
#################

from tenacity import retry_if_exception_type
from tenacity import stop_after_attempt
from tenacity import wait_exponential
from tenacity import retry
from datetime import timezone
from datetime import datetime
from fastapi import HTTPException
import requests
from backend.config import BRAPI_TOKEN, API_URL

class BrapiService:
    def __init__(self):
        self.token = BRAPI_TOKEN
        self.api_url = API_URL

    def _convert_unix_to_iso(self, data):
        """Converte timestamps UNIX ou ajusta strings ISO 8601 para usar 'Z' se em UTC."""
        if 'results' in data:
            for result in data['results']:
                if 'historicalDataPrice' in result:
                    for price in result['historicalDataPrice']:
                        if 'date' in price:
                            if isinstance(price['date'], (int, float)):  # Timestamp UNIX
                                dt = datetime.fromtimestamp(price['date'], tz=timezone.utc)
                                price['date'] = dt.isoformat().replace('+00:00', 'Z')  # Converte e substitui
                            elif isinstance(price['date'], str):  # Já é string ISO 8601
                                if price['date'].endswith('+00:00'):
                                    price['date'] = price['date'].replace('+00:00', 'Z')  # Ajusta para 'Z' se UTC
                                # Se for outro fuso horário (ex.: "-03:00"), mantém como está
        return data

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=10),  # Intervalo exponencial: 1s, 2s, 4s, até 10s
        stop=stop_after_attempt(3),  # Máximo de 3 tentativas
        retry=retry_if_exception_type(requests.exceptions.RequestException)  # Retentar apenas em falhas de requisição
    )
    def _make_request(self, endpoint, params):
            """Método auxiliar para fazer requisições à API externa com resiliência."""
            url = f'{self.api_url}/{endpoint}'
            params['token'] = self.token
            try:
                response = requests.get(url, params=params, timeout=10)  # Timeout de 10 segundos
                response.raise_for_status()  # Levanta exceção para status 4xx ou 5xx
                data = response.json()
                if not data:
                    raise HTTPException(status_code=404, detail="No data available")
                return self._convert_unix_to_iso(data)  # Converte as datas antes de retornar
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    raise HTTPException(status_code=404, detail="No data available")
                else:
                    raise HTTPException(status_code=e.response.status_code, detail="Failed to fetch data from API")
            except requests.exceptions.RequestException as e:
                raise HTTPException(status_code=500, detail="Failed to fetch data from API")
        
    def get_available_assets(self, search: str = ''):
        params = {'search': search}
        return self._make_request('available', params)

    def get_ticker_quote(self, ticker: str, range: str = '1d', interval: str = '', fundamental: str = 'false', dividends: str = 'false', modules: str = ''):
        endpoint = f'quote/{ticker}'
        params = {
            'range': range,
            'interval': interval,
            'fundamental': fundamental,
            'dividends': dividends,
            'modules': modules,
        }
        return self._make_request(endpoint, params)

    def get_quote_list(self, search: str = '', sortBy: str = '', sortOrder: str = '', limit: int = 0, sector: str = ''):
        params = {
            'search': search,
            'sortBy': sortBy,
            'sortOrder': sortOrder,
            'limit': limit if limit > 0 else '',
            'sector': sector,
        }
        data = self._make_request('quote/list', params)
        if isinstance(data, dict) and 'stocks' in data and not data['stocks']:
            return {'error': 'No data available'}
        return data