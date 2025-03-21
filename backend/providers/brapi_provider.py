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
from backend.models import AssetList, HistoricalPrice, PricePoint, TimeRange, APIError
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
                raise HTTPException(
                    status_code=404,
                    detail=APIError(
                        code="NO_DATA_AVAILABLE",
                        message="Nenhum dado disponível",
                        details={"endpoint": endpoint, "ticker": params.get('ticker', '')}
                    ).model_dump()
                )
            
            return data
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=APIError(
                        code="NO_DATA_AVAILABLE",
                        message="Nenhum dado disponível",
                        details={"endpoint": endpoint, "ticker": params.get('ticker', '')}
                    ).model_dump()
                )
            else:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=APIError(
                        code="API_ERROR",
                        message=f"Erro ao buscar dados da API: {str(e)}",
                        details={"status_code": e.response.status_code, "ticker": params.get('ticker', '')}
                    ).model_dump()
                )
                
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500,
                detail=APIError(
                    code="REQUEST_ERROR",
                    message=f"Erro ao fazer requisição: {str(e)}",
                    details={"error": str(e), "ticker": params.get('ticker', '')}
                ).model_dump()
            )
    
    async def get_available_assets(self, search: Optional[str] = None) -> AssetList:
        """Retorna uma lista de ativos disponíveis."""
        params = {'search': search or ''}
        data = await self._make_request('available', params)
        
        return AssetList(
            indexes=data.get('indexes', []),
            stocks=data.get('stocks', [])
        )