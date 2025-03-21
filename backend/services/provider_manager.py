from typing import Dict, Type, AsyncGenerator
from contextlib import asynccontextmanager

from backend.providers.base import MarketDataProvider
from backend.providers.brapi_provider import BrapiProvider
from backend.providers.yahoo_provider import YahooProvider


class ProviderManager:
    """
    Gerencia os diferentes provedores de dados de mercado.
    Implementa o padrão Factory para criar provedores conforme necessário.
    """
    
    def __init__(self):
        self._providers: Dict[str, Type[MarketDataProvider]] = {
            'brapi': BrapiProvider,
            'yahoo': YahooProvider
        }
        # Provedores padrão por rota
        self._default_providers: Dict[str, str] = {
            'get_available_assets': 'brapi',
            'get_historical_prices': 'yahoo'
        }
    
    def register_provider(self, name: str, provider_class: Type[MarketDataProvider]) -> None:
        """
        Registra um novo provedor.
        
        Args:
            name: Nome do provedor.
            provider_class: Classe do provedor que implementa MarketDataProvider.
        """
        self._providers[name] = provider_class
    
    def set_default_provider_for_route(self, route_name: str, provider_name: str) -> None:
        """
        Define o provedor padrão para uma rota específica.
        
        Args:
            route_name: Nome da rota (ex: 'get_available_assets', 'get_historical_prices').
            provider_name: Nome do provedor.
            
        Raises:
            ValueError: Se o provedor não estiver registrado.
        """
        if provider_name not in self._providers:
            raise ValueError(f"Provider '{provider_name}' not registered")
        self._default_providers[route_name] = provider_name
    
    @asynccontextmanager
    async def get_provider(self, provider_name: str = None, route_name: str = None) -> AsyncGenerator[MarketDataProvider, None]:
        """
        Retorna uma instância do provedor solicitado.
        
        Args:
            provider_name: Nome do provedor. Se None, usa o provedor padrão da rota.
            route_name: Nome da rota para determinar o provedor padrão.
            
        Returns:
            Uma instância do provedor implementando MarketDataProvider.
            
        Raises:
            ValueError: Se o provedor não estiver registrado.
        """
        if provider_name is None and route_name is not None:
            provider_name = self._default_providers.get(route_name, 'brapi')
        
        if provider_name not in self._providers:
            raise ValueError(f"Provider '{provider_name}' not registered")
        
        provider_class = self._providers[provider_name]
        provider = provider_class()
        
        try:
            await provider.__aenter__()
            yield provider
        finally:
            await provider.__aexit__(None, None, None)


# Instância global do gerenciador de provedores
provider_manager = ProviderManager()