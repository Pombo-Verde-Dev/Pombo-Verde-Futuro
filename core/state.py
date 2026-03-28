"""
No inicio eu peguei do gpt essa logica de state sem nem entender como funcionava
Basicamente, o state é um objeto que guarda o estado da conexão, tipo o usuário logado
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from functools import cached_property

from .config import get_config
from .http import HTTPClient
from .cache import Cache

if TYPE_CHECKING:
    from ..models.user import User
    from ..generator.gemini import Generator

__all__ = ("ConnectionState",)


class ConnectionState:
    def __init__(
        self,
        http: HTTPClient,
        user: User,
        token: str,
        generator: Generator | None = None,
    ) -> None:
        self.http = http
        self.user = user
        self._token = token
        self._generator = generator
        self._cache = Cache()
        self._closed = False

    @property
    def is_closed(self) -> bool:
        return self._closed

    @cached_property
    def config(self):
        return get_config()

    def get_targets(self, room_name: str) -> list[str]:
        targets = [room_name]
        if self.user.username:
            targets.append(f"{room_name}:{self.user.username}-sp")
        targets.extend(self.config.EXTRA_TARGETS)
        return targets

    async def close(self) -> None:
        if self._closed:
            return

        await self._cache.clear()
        await self.http.close()
        self._closed = True

    def __repr__(self) -> str:
        return f"<ConnectionState user={self.user!r}>"