from __future__ import annotations

from typing import Protocol, runtime_checkable, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .enums import Area, Prioridade, Categoria, TipoAcao

__all__ = (
    "MensagemProtocol",
    "Cacheable",
    "Identifiable",
    "Timestamped",
    "JSON",
)

JSON = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None


@runtime_checkable
class Identifiable(Protocol):
    """Protocolo para objetos que possuem um ID único"""
    @property
    def id(self) -> int | str: ...


@runtime_checkable
class Timestamped(Protocol):
    """ Protocolo para objetos que possuem um timestamp de criação """
    @property
    def created_at(self) -> datetime: ...


@runtime_checkable
class MensagemProtocol(Protocol):
    """Protocolo para mensagens como notificações e avisos"""
    @property
    def msg_id(self) -> int: ...

    @property
    def msg_titulo(self) -> str: ...

    @property
    def msg_texto(self) -> str: ...

    @property
    def msg_data(self) -> datetime: ...

    @property
    def msg_lida(self) -> bool: ...

    @property
    def msg_origem(self) -> str: ...

    @property
    def tempo_atras(self) -> str: ...

    async def ler(self) -> bool: ...


@runtime_checkable
class Cacheable(Protocol):
    """Protocolo para objetos que podem ser cacheados (amo cache)"""
    @property
    def cache_key(self) -> str: ...

    @property
    def cache_ttl(self) -> int: ...