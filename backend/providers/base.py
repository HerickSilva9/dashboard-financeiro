from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from backend.models import AssetList, HistoricalPrice, TimeRange


class MarketDataProvider(ABC):
    """Interface base para provedores de dados de mercado."""
    
    def get_available_assets(self, search: Optional[str] = None) -> AssetList:
        """
        Retorna uma lista de ativos disponíveis.
        Método opcional - implementação padrão retorna lista vazia.
        
        Args:
            search: Termo de busca opcional para filtrar os resultados.
            
        Returns:
            AssetList: Lista de ativos encontrados.
        """
        return AssetList(indexes=[], stocks=[])
    
    def get_historical_prices(self, ticker: str, time_range: TimeRange) -> HistoricalPrice:
        """
        Retorna preços históricos para um ticker específico.
        Método opcional - implementação padrão retorna lista vazia.
        
        Args:
            ticker: Símbolo do ativo.
            time_range: Configuração de intervalo de tempo.
            
        Returns:
            HistoricalPrice: Dados históricos de preços.
        """
        return HistoricalPrice(
            symbol=ticker,
            name=ticker,
            currency="BRL",
            prices=[]
        )