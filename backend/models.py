from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime


class AssetList(BaseModel):
    """Modelo para lista de ativos disponíveis."""
    indexes: List[str] = Field(default_factory=list)
    stocks: List[str] = Field(default_factory=list)


class PricePoint(BaseModel):
    """Modelo para um ponto de dados de preço."""
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class HistoricalPrice(BaseModel):
    """Modelo para preços históricos de um ativo."""
    symbol: str
    name: Optional[str] = None
    currency: Optional[str] = None
    prices: List[PricePoint] = Field(default_factory=list)
    

class APIError(BaseModel):
    """Modelo para erros da API."""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class APIResponse(BaseModel):
    """Modelo base para todas as respostas da API."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[APIError] = None


class TimeRange(BaseModel):
    """Modelo para definir intervalo de tempo para consulta de dados."""
    range: str = "1d"  # Padrão: 1 dia
    interval: Optional[str] = None  # Intervalo entre pontos de dados