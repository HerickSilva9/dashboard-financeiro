from typing import Any, Dict, Optional, TypeVar, Generic
from datetime import datetime, UTC
from zoneinfo import ZoneInfo
from pydantic import BaseModel, Field

from backend.models import APIResponse, APIError

T = TypeVar('T')

class ResponseData(BaseModel, Generic[T]):
    """Modelo genérico para dados de resposta."""
    data: T
    metadata: Optional[Dict[str, Any]] = None

class ResponseUtil:
    """Classe utilitária para criar respostas padronizadas da API."""
    
    LOCAL_TIMEZONE = ZoneInfo("America/Sao_Paulo")
    
    @staticmethod
    def _format_timestamp(dt: datetime) -> str:
        """
        Formata o timestamp no fuso horário local, sem microssegundos e com Z.
        """
        local_dt = dt.astimezone(ResponseUtil.LOCAL_TIMEZONE)
        return local_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    @staticmethod
    def _get_timezone_info() -> Dict[str, Any]:
        """Retorna informações sobre timezone."""
        local_tz = ResponseUtil.LOCAL_TIMEZONE
        utc_now = datetime.now(UTC)
        local_now = utc_now.astimezone(local_tz)
        
        return {
            "timezone": {
                "name": "America/Sao_Paulo",
                "offset": local_now.utcoffset().total_seconds() / 3600,
                "is_dst": local_now.dst().total_seconds() > 0
            }
        }
    
    @staticmethod
    def success(data: Any = None, message: str = None, metadata: Dict[str, Any] = None) -> APIResponse:
        """
        Cria uma resposta de sucesso.
        
        Args:
            data: Dados principais da resposta
            message: Mensagem opcional de sucesso
            metadata: Metadados adicionais
        """
        metadata = metadata or {}
        metadata.update(ResponseUtil._get_timezone_info())
        
        response_data = {
            "timestamp": ResponseUtil._format_timestamp(datetime.now(UTC)),
            "message": message
        }
        
        if data is not None:
            response_data["content"] = data
            
        if metadata:
            response_data["metadata"] = metadata
            
        return APIResponse(
            success=True,
            data=response_data
        )
    
    @staticmethod
    def error(
        code: str,
        message: str,
        details: Dict[str, Any] = None,
        status_code: int = None
    ) -> APIResponse:
        """
        Cria uma resposta de erro.
        
        Args:
            code: Código do erro
            message: Mensagem de erro
            details: Detalhes adicionais do erro
            status_code: Código de status HTTP
        """
        details = details or {}
        details.update(ResponseUtil._get_timezone_info())
        
        error = APIError(
            code=code,
            message=message,
            details={
                "timestamp": ResponseUtil._format_timestamp(datetime.now(UTC)),
                **details,
                **({"status_code": status_code} if status_code else {})
            }
        )
        
        return APIResponse(
            success=False,
            error=error
        )
    
    @staticmethod
    def pagination_metadata(
        total_items: int,
        page: int,
        items_per_page: int,
        total_pages: int
    ) -> Dict[str, Any]:
        """
        Cria metadados para respostas paginadas.
        """
        return {
            "pagination": {
                "total_items": total_items,
                "page": page,
                "items_per_page": items_per_page,
                "total_pages": total_pages
            }
        } 