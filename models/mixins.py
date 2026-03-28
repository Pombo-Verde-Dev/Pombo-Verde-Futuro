"""Mixin para funcionalidades comuns a vários modelos, como serialização, acesso à API, etc."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING
from datetime import datetime, date, time
import json

if TYPE_CHECKING:
    from ..core.state import ConnectionState

__all__ = (
    "SerializableMixin",
    "TimestampMixin",
    "CacheableMixin",
    "APIAccessibleMixin",
)

_SERIALIZABLE_TYPES = (datetime, date, time)


class SerializableMixin:
    """Mixin pra serializar em JSON.

    Funciona com classe __dict__ e com __slots__.
    """

    def _get_serializable_attrs(self) -> dict[str, Any]:
        """Pega os atributos serializáveis de __dict__ ou __slots__."""
        result: dict[str, Any] = {}

        if hasattr(self, '__dict__'):
            for key, value in self.__dict__.items():
                if not key.startswith('_'):
                    result[key] = value

        slots = getattr(self, '__slots__', ())
        for slot in slots:
            if not slot.startswith('_') and hasattr(self, slot):
                result[slot] = getattr(self, slot)

        return result

    def _serialize_value(self, value: Any) -> Any:
        """Serializa um valor só."""
        if isinstance(value, _SERIALIZABLE_TYPES):
            return value.isoformat()
        if isinstance(value, (list, tuple)):
            return [self._serialize_value(v) for v in value]
        if isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        if hasattr(value, 'to_dict'):
            return value.to_dict()
        return value

    def to_dict(self) -> dict[str, Any]:
        """Converte pra dicionário."""
        return {
            k: self._serialize_value(v)
            for k, v in self._get_serializable_attrs().items()
        }

    def to_json(self, indent: int | None = None) -> str:
        """Converte pra JSON."""
        return json.dumps(self.to_dict(), indent=indent, default=str)


class TimestampMixin:
    """Mixin pra coisas com timestamp."""

    @property
    def tempo_atras(self) -> str:
        """String de tempo relativo."""
        from ..utils import format_relative_time
        return format_relative_time(self.created_at)

    @property
    def is_recent(self) -> bool:
        """Diz se foi criado nas últimas 24h."""
        return (datetime.now() - self.created_at).days < 1


class CacheableMixin:
    """Mixin pra objetos cacheáveis."""

    @property
    def cache_key(self) -> str:
        """Gera chave de cache."""
        return f"{self.__class__.__name__.lower()}:{getattr(self, 'id', 'unknown')}"

    @property
    def cache_ttl(self) -> int:
        """TTL padrão do cache."""
        return 300


class APIAccessibleMixin:
    """Mixin pra objetos que falam com API."""

    _state: ConnectionState | None = None

    def _bind_state(self, state: ConnectionState | None) -> None:
        """Vincula ao state de conexão. Chama no __init__."""
        self._state = state

    @property
    def _http(self):
        """Acessa o cliente HTTP."""
        if self._state is None:
            raise RuntimeError(
                f"{self.__class__.__name__} not bound to connection state"
            )
        return self._state.http

    async def _api_get(self, url: str, **kwargs) -> Any:
        """Faz requisição GET."""
        return await self._http.get(url, **kwargs)

    async def _api_post(self, url: str, **kwargs) -> Any:
        """Faz requisição POST."""
        return await self._http.post(url, **kwargs)

    async def _api_put(self, url: str, **kwargs) -> Any:
        """Faz requisição PUT."""
        return await self._http.put(url, **kwargs)