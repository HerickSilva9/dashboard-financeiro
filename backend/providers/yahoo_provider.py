from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import yfinance as yf
from fastapi import HTTPException
import requests.exceptions
import logging

from backend.providers.base import MarketDataProvider
from backend.models import AssetList, HistoricalPrice, PricePoint, TimeRange, APIError


class YahooProvider(MarketDataProvider):
    """Implementação do provedor de dados Yahoo Finance."""
    
    def __init__(self):
        self.client = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    
    def _convert_yahoo_range(self, range: str) -> str:
        """Converte o range do formato da API para o formato do Yahoo Finance."""
        range_map = {
            "1d": "1d",
            "5d": "5d",
            "1mo": "1mo",
            "3mo": "3mo",
            "6mo": "6mo",
            "1y": "1y",
            "2y": "2y",
            "5y": "5y",
            "10y": "10y",
            "ytd": "ytd",
            "max": "max"
        }
        return range_map.get(range, "1d")

    def _convert_yahoo_interval(self, interval: Optional[str]) -> str:
        """Converte o intervalo do formato da API para o formato do Yahoo Finance."""
        if not interval:
            return "1d"
        
        interval_map = {
            "1m": "1m",
            "5m": "5m",
            "15m": "15m",
            "30m": "30m",
            "1h": "1h",
            "1d": "1d",
            "1wk": "1wk",
            "1mo": "1mo"
        }
        return interval_map.get(interval, "1d")
    
    async def get_historical_prices(self, ticker: str, time_range: TimeRange) -> HistoricalPrice:
        """Retorna preços históricos para um ticker específico."""
        original_ticker = ticker
        # Adiciona sufixo .SA para ações brasileiras se não estiver presente
        if not ticker.endswith('.SA'):
            ticker = f"{ticker}.SA"
        
        try:
            # Obtém os dados do Yahoo Finance
            try:
                yf_ticker = yf.Ticker(ticker)
                info = yf_ticker.info
            except Exception as e:
                logging.error(f"Erro ao buscar dados do ticker {ticker}: {str(e)}")
                raise HTTPException(
                    status_code=404,
                    detail=APIError(
                        code="ASSET_NOT_FOUND",
                        message=f"Ativo {ticker} não encontrado",
                        details={"ticker": ticker}
                    ).model_dump()
                )
            
            if not info or not info.get('regularMarketPrice'):
                raise HTTPException(
                    status_code=404,
                    detail=APIError(
                        code="ASSET_NOT_FOUND",
                        message=f"Ativo {ticker} não encontrado",
                        details={"ticker": ticker}
                    ).model_dump()
                )
            
            # Converte os parâmetros de tempo
            interval = self._convert_yahoo_interval(time_range.interval)
            period = self._convert_yahoo_range(time_range.range)
            
            # Obtém os dados históricos
            try:
                hist = yf_ticker.history(period=period, interval=interval)
            except Exception as e:
                logging.error(f"Erro ao buscar histórico do ticker {ticker}: {str(e)}")
                raise HTTPException(
                    status_code=404,
                    detail=APIError(
                        code="ASSET_NOT_FOUND",
                        message=f"Ativo {ticker} não encontrado",
                        details={"ticker": ticker}
                    ).model_dump()
                )
            
            if hist.empty:
                raise HTTPException(
                    status_code=404,
                    detail=APIError(
                        code="NO_DATA_AVAILABLE",
                        message=f"Nenhum dado disponível para o ativo {ticker}",
                        details={
                            "ticker": ticker,
                            "period": period,
                            "interval": interval
                        }
                    ).model_dump()
                )
            
            # Converte os dados para o formato esperado
            prices: List[PricePoint] = []
            for date, row in hist.iterrows():
                price_point = PricePoint(
                    date=date,
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume'])
                )
                prices.append(price_point)
            
            return HistoricalPrice(
                symbol=ticker,
                name=info.get('longName', ticker),
                currency=info.get('currency', 'BRL'),
                prices=prices
            )
            
        except HTTPException:
            # Propaga exceções HTTP (já formatadas)
            raise
        except Exception as e:
            # Captura qualquer outra exceção inesperada
            logging.error(f"Erro não tratado ao buscar dados do ticker {ticker}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=APIError(
                    code="INTERNAL_ERROR",
                    message="Erro ao buscar dados do Yahoo Finance",
                    details={"error": str(e), "ticker": ticker}
                ).model_dump()
            ) 