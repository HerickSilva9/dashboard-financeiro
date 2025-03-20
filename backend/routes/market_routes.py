from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional

from backend.models import AssetList, HistoricalPrice, TimeRange, APIResponse
from backend.services.provider_manager import provider_manager


router = APIRouter(prefix="/market", tags=["market"])


@router.get("/assets", response_model=APIResponse)
async def get_available_assets(
    search: Optional[str] = Query(None, description="Termo de busca para filtrar ativos"),
    provider: Optional[str] = Query(None, description="Nome do provedor de dados a ser usado")
):
    """
    Retorna a lista de ativos disponíveis.
    
    Args:
        search: Termo de busca opcional para filtrar os resultados.
        provider: Nome do provedor de dados (opcional).
        
    Returns:
        APIResponse contendo a lista de ativos.
    """
    try:
        async with provider_manager.get_provider(provider) as data_provider:
            assets = await data_provider.get_available_assets(search)
            return APIResponse(
                success=True,
                data=assets
            )
    except ValueError as e:
        return APIResponse(
            success=False,
            error=str(e)
        )
    except HTTPException as e:
        return APIResponse(
            success=False,
            error=e.detail
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error=f"Unexpected error: {str(e)}"
        )


@router.get("/prices/{ticker}", response_model=APIResponse)
async def get_historical_prices(
    ticker: str,
    range: str = Query("1d", description="Intervalo de tempo para os dados históricos"),
    interval: Optional[str] = Query(None, description="Intervalo entre pontos de dados"),
    provider: Optional[str] = Query(None, description="Nome do provedor de dados a ser usado")
):
    """
    Retorna os preços históricos para um ativo específico.
    
    Args:
        ticker: Símbolo do ativo.
        range: Intervalo de tempo para os dados históricos (ex: 1d, 5d, 1mo, 1y).
        interval: Intervalo entre pontos de dados (ex: 1m, 5m, 1h, 1d).
        provider: Nome do provedor de dados (opcional).
        
    Returns:
        APIResponse contendo os dados históricos de preços.
    """
    try:
        time_range = TimeRange(range=range, interval=interval)
        
        async with provider_manager.get_provider(provider) as data_provider:
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
    except ValueError as e:
        return APIResponse(
            success=False,
            error=str(e)
        )
    except HTTPException as e:
        return APIResponse(
            success=False,
            error=e.detail
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error=f"Unexpected error: {str(e)}"
        )