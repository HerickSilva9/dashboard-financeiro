from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from fastapi.responses import JSONResponse
from fastapi import status

from backend.models import AssetList, HistoricalPrice, TimeRange, APIResponse, APIError
from backend.services.provider_manager import provider_manager


router = APIRouter(prefix="/market", tags=["market"])


@router.get("/assets", response_model=APIResponse)
async def get_available_assets(
    search: Optional[str] = Query(None, description="Termo de busca para filtrar ativos")
):
    """
    Retorna a lista de ativos disponíveis.
    
    Args:
        search: Termo de busca opcional para filtrar os resultados.
        
    Returns:
        APIResponse contendo a lista de ativos.
    """
    try:
        async with provider_manager.get_provider(route_name='get_available_assets') as data_provider:
            assets = await data_provider.get_available_assets(search)
            return APIResponse(
                success=True,
                data=assets.dict()
            )
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=APIResponse(
                success=False,
                error=APIError(**e.detail)
            ).dict()
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=APIResponse(
                success=False,
                error=APIError(
                    code="INTERNAL_ERROR",
                    message="Erro interno do servidor",
                    details={"error": str(e)}
                )
            ).dict()
        )


@router.get("/prices/{ticker}", response_model=APIResponse)
async def get_historical_prices(
    ticker: str,
    range: str = Query("1d", description="Intervalo de tempo para os dados históricos"),
    interval: Optional[str] = Query(None, description="Intervalo entre pontos de dados")
):
    """
    Retorna os preços históricos para um ativo específico.
    
    Args:
        ticker: Símbolo do ativo.
        range: Intervalo de tempo para os dados históricos (ex: 1d, 5d, 1mo, 1y).
        interval: Intervalo entre pontos de dados (ex: 1m, 5m, 1h, 1d).
        
    Returns:
        APIResponse contendo os dados históricos de preços.
    """
    try:
        time_range = TimeRange(range=range, interval=interval)
        
        async with provider_manager.get_provider(route_name='get_historical_prices') as data_provider:
            prices = await data_provider.get_historical_prices(ticker, time_range)
            return APIResponse(
                success=True,
                data={
                    "results": [{
                        "symbol": prices.symbol,
                        "longName": prices.name,
                        "currency": prices.currency,
                        "historicalDataPrice": [
                            {
                                "date": int(price.date.timestamp()),
                                "open": price.open,
                                "high": price.high,
                                "low": price.low,
                                "close": price.close,
                                "volume": price.volume
                            }
                            for price in prices.prices
                        ]
                    }]
                }
            )
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=APIResponse(
                success=False,
                error=APIError(**e.detail)
            ).dict()
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=APIResponse(
                success=False,
                error=APIError(
                    code="INTERNAL_ERROR",
                    message="Erro interno do servidor",
                    details={"error": str(e)}
                )
            ).dict()
        )