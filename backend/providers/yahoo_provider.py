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

    def _get_ticker_info(self, ticker: str) -> Dict[str, Any]:
        """Método auxiliar para obter informações do ticker e tratar erros comuns."""
        if not ticker.endswith('.SA'):
            ticker = f"{ticker}.SA"
        
        try:
            yf_ticker = yf.Ticker(ticker)
            info = yf_ticker.info
            
            if not info:
                raise HTTPException(
                    status_code=404,
                    detail=APIError(
                        code="ASSET_NOT_FOUND",
                        message=f"Ativo {ticker} não encontrado",
                        details={"ticker": ticker}
                    ).model_dump()
                )
            
            return info
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

    async def get_fundamental_indicators(self, ticker: str) -> Dict[str, Any]:
        """Retorna indicadores fundamentalistas para um ticker específico."""
        info = self._get_ticker_info(ticker)
        
        return {
            "pe_ratio": info.get("forwardPE"),
            "pb_ratio": info.get("priceToBook"),
            "dividend_yield": info.get("dividendYield"),
            "roe": info.get("returnOnEquity"),
            "ebitda_margins": info.get("ebitdaMargins"),
            "debt_to_equity": info.get("debtToEquity"),
            "gross_margins": info.get("grossMargins"),
            "profit_margins": info.get("profitMargins")
        }

    async def get_market_data(self, ticker: str) -> Dict[str, Any]:
        """Retorna dados de mercado para um ticker específico."""
        info = self._get_ticker_info(ticker)
        
        return {
            "market_cap": info.get("marketCap"),
            "average_volume": info.get("averageVolume"),
            "beta": info.get("beta"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "short_ratio": info.get("shortRatio"),
            "regular_market_price": info.get("regularMarketPrice"),
            "regular_market_volume": info.get("regularMarketVolume")
        }

    async def get_analyst_info(self, ticker: str) -> Dict[str, Any]:
        """Retorna informações de analistas para um ticker específico."""
        info = self._get_ticker_info(ticker)
        
        return {
            "target_mean_price": info.get("targetMeanPrice"),
            "recommendation": info.get("recommendationKey"),
            "number_of_analysts": info.get("numberOfAnalystOpinions"),
            "earnings_growth": info.get("earningsGrowth"),
            "revenue_growth": info.get("revenueGrowth"),
            "recommendation_mean": info.get("recommendationMean")
        }

    async def get_market_indicators(self, ticker: str) -> Dict[str, Any]:
        """Retorna todos os indicadores de mercado para um ticker específico."""
        result = {}
        errors = []
        not_found_error = None

        try:
            # Tenta obter dados fundamentalistas
            try:
                result["fundamentals"] = await self.get_fundamental_indicators(ticker)
            except HTTPException as e:
                if e.status_code == 404:
                    not_found_error = e
                logging.error(f"Erro ao buscar indicadores fundamentalistas para {ticker}: {str(e)}")
                errors.append("fundamentals")
                result["fundamentals"] = None

            # Tenta obter dados de mercado
            try:
                result["market_data"] = await self.get_market_data(ticker)
            except HTTPException as e:
                if e.status_code == 404:
                    not_found_error = e
                logging.error(f"Erro ao buscar dados de mercado para {ticker}: {str(e)}")
                errors.append("market_data")
                result["market_data"] = None

            # Tenta obter dados de analistas
            try:
                result["analyst_info"] = await self.get_analyst_info(ticker)
            except HTTPException as e:
                if e.status_code == 404:
                    not_found_error = e
                logging.error(f"Erro ao buscar informações de analistas para {ticker}: {str(e)}")
                errors.append("analyst_info")
                result["analyst_info"] = None

            # Se todos os métodos falharam e temos um erro 404, propaga o erro
            if len(errors) == 3 and not_found_error:
                raise not_found_error

            # Se todos os métodos falharam com outros erros, lança exceção 500
            if len(errors) == 3:
                raise HTTPException(
                    status_code=500,
                    detail=APIError(
                        code="INDICATORS_UNAVAILABLE",
                        message="Não foi possível obter nenhum indicador",
                        details={
                            "ticker": ticker,
                            "failed_sections": errors
                        }
                    ).model_dump()
                )

            # Se alguns métodos falharam, inclui informação nos metadados
            if errors:
                result["_metadata"] = {
                    "failed_sections": errors,
                    "partial_data": True
                }

            return result

        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"Erro não tratado ao buscar indicadores do ticker {ticker}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=APIError(
                    code="INTERNAL_ERROR",
                    message="Erro ao buscar indicadores do Yahoo Finance",
                    details={"error": str(e), "ticker": ticker}
                ).model_dump()
            ) 