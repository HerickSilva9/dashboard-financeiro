from typing import Dict, Type, AsyncGenerator
from contextlib import asynccontextmanager

from backend.providers.base import MarketDataProvider
from backend.providers.brapi_provider import BrapiProvider


class ProviderManager:
    """
    Gerencia os diferentes provedores de dados de mercado.
    Implementa o padrão Factory para criar provedores conforme necessário.
    """
    
    def __init__(self):
        self._providers: Dict[str, Type[MarketDataProvider]] = {
            'brapi': BrapiProvider
        }
        self._default_provider = 'brapi'
    
    def register_provider(self, name: str, provider_class: Type[MarketDataProvider]) -> None:
        """
        Registra um novo provedor.
        
        Args:
            name: Nome do provedor.
            provider_class: Classe do provedor que implementa MarketDataProvider.
        """
        self._providers[name] = provider_class
    
    def set_default_provider(self, name: str) -> None:
        """
        Define o provedor padrão.
        
        Args:
            name: Nome do provedor.
            
        Raises:
            ValueError: Se o provedor não estiver registrado.
        """
        if name not in self._providers:
            raise ValueError(f"Provider '{name}' not registered")
        self._default_provider = name
    
    @asynccontextmanager
    async def get_provider(self, provider_name: str = None) -> AsyncGenerator[MarketDataProvider, None]:
        """
        Retorna uma instância do provedor solicitado.
        
        Args:
            provider_name: Nome do provedor. Se None, usa o provedor padrão.
            
        Returns:
            Uma instância do provedor implementando MarketDataProvider.
            
        Raises:
            ValueError: Se o provedor não estiver registrado.
        """
        name = provider_name or self._default_provider
        
        if name not in self._providers:
            raise ValueError(f"Provider '{name}' not registered")
        
        provider_class = self._providers[name]
        provider = provider_class()
        
        try:
            await provider.__aenter__()
            yield provider
        finally:
            await provider.__aexit__(None, None, None)


# Instância global do gerenciador de provedores
provider_manager = ProviderManager()