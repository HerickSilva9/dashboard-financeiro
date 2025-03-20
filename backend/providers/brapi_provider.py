from datetime import datetime
from typing import Optional, Dict, List, Any
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from fastapi import HTTPException

from backend.providers.base import MarketDataProvider
from backend.models import AssetList, HistoricalPrice, PricePoint, TimeRange
from backend.config import BRAPI_TOKEN, API_URL


class BrapiProvider(MarketDataProvider):
    """Implementação do provedor de dados BrAPI."""
    
    def __init__(self):
        self.token = BRAPI_TOKEN
        self.api_url = API_URL
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def _convert_unix_to_datetime(self, timestamp) -> datetime:
        """Converte timestamp UNIX para objeto datetime."""
        if isinstance(timestamp, (int, float)):
            return datetime.fromtimestamp(timestamp)
        return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    
    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(httpx.RequestError)
    )
    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Método auxiliar para fazer requisições à API externa com resiliência."""
        url = f'{self.api_url}/{endpoint}'
        params['token'] = self.token
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                raise HTTPException(status_code=404, detail="No data available")
            
            return data
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(status_code=404, detail="No data available")
            else:
                raise HTTPException(
                    status_code=e.response.status_code, 
                    detail=f"Failed to fetch data from API: {str(e)}"
                )
                
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to fetch data from API: {str(e)}"
            )
    
    async def get_available_assets(self, search: Optional[str] = None) -> AssetList:
        """Retorna uma lista de ativos disponíveis."""
        params = {'search': search or ''}
        data = await self._make_request('available', params)
        
        return AssetList(
            indexes=data.get('indexes', []),
            stocks=data.get('stocks', [])
        )
    
    async def get_historical_prices(self, ticker: str, time_range: TimeRange) -> HistoricalPrice:
        """Retorna preços históricos para um ticker específico."""
        endpoint = f'quote/{ticker}'
        params = {
            'range': time_range.range,
            'interval': time_range.interval or '',
            'fundamental': 'false',
            'dividends': 'false'
        }
        
        data = await self._make_request(endpoint, params)
        
        # Verificar se há resultados válidos na resposta
        if 'results' not in data or not data['results']:
            raise HTTPException(status_code=404, detail=f"No data available for ticker {ticker}")
        
        result = data['results'][0]
        name = result.get('longName', ticker)
        currency = result.get('currency', 'BRL')
        
        prices: List[PricePoint] = []
        
        if 'historicalDataPrice' in result:
            for price_data in result['historicalDataPrice']:
                try:
                    # Converter e validar dados
                    date_value = self._convert_unix_to_datetime(price_data['date'])
                    
                    price_point = PricePoint(
                        date=date_value,
                        open=float(price_data.get('open', 0)),
                        high=float(price_data.get('high', 0)),
                        low=float(price_data.get('low', 0)),
                        close=float(price_data.get('close', 0)),
                        volume=int(price_data.get('volume', 0))
                    )
                    prices.append(price_point)
                except (ValueError, KeyError) as e:
                    # Ignore dados inválidos, mas registre para depuração
                    print(f"Erro ao processar ponto de preço: {str(e)}")
                    continue
        
        return HistoricalPrice(
            symbol=ticker,
            name=name,
            currency=currency,
            prices=prices
        )