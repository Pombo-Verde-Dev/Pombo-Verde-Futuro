"""
Sistema de cache simples para armazenar resultados de chamadas da api e outros dados
Esse sistema é meio simples, copiei de um projeto antigo meu

Basicamente a logica do cache é a mesma pra quase todos os sistemas

Resulmidamente ele funciona assim:
1. Tem uma classe CacheEntry que guarda o valor, a data de criação, a quantidade de acessos e a data do ultimo acesso
2. Tem uma classe Cache que guarda um dicionário de chaves para CacheEntry, e tem métodos para pegar, setar, deletar e limpar o cache, além de um método para invalidar chaves por padrão
3. Tem um decorator cached que pode ser usado pra decorar funções e armazenar os resultados no cache automaticamente, usando uma chave gerada a partir dos argumentos da função
4. O cache tem um sistema de TTL para expirar os dados
5. O cache tem um sistema de tamanho máximo, e quando atinge o limite ele remove os itens mais antigos
6. O cache tem estatísticas de hits, misses e hit rate
7. O cache é thread-safe usando um lock assíncrono
"""

from __future__ import annotations

import asyncio
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar, Callable
from functools import wraps
import logging

from .errors import CacheError

__all__ = ("Cache", "cached", "CacheEntry")

T = TypeVar("T")
logger = logging.getLogger(__name__)


@dataclass
class CacheEntry(Generic[T]):
    value: T
    created_at: float = field(default_factory=time.time)
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)


class Cache(Generic[T]):
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: int = 300,
        enabled: bool = True,
    ) -> None:
        self._cache: OrderedDict[str, CacheEntry[T]] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._enabled = enabled
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0

    @property
    def stats(self) -> dict[str, Any]:
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.2%}",
        }

    def _is_expired(self, entry: CacheEntry[T]) -> bool:
        return time.time() - entry.created_at > self._default_ttl

    async def get(self, key: str) -> T | None:
        if not self._enabled:
            return None

        async with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._misses += 1
                return None

            if self._is_expired(entry):
                del self._cache[key]
                self._misses += 1
                return None

            entry.access_count += 1
            entry.last_accessed = time.time()

            self._cache.move_to_end(key)

            self._hits += 1
            return entry.value

    async def set(
        self,
        key: str,
        value: T,
        ttl: int | None = None,
    ) -> None:
        if not self._enabled:
            return

        async with self._lock:
            if len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)

            self._cache[key] = CacheEntry(value=value)

    async def delete(self, key: str) -> bool:
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def clear(self) -> None:
        async with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    async def invalidate_pattern(self, pattern: str) -> int:
        async with self._lock:
            to_delete = [k for k in self._cache if pattern in k]
            for k in to_delete:
                del self._cache[k]
            return len(to_delete)


def cached(
    ttl: int = 300,
    key_prefix: str = "",
    max_size: int = 1000,
) -> Callable:
    cache = Cache(max_size=max_size, default_ttl=ttl)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            key_parts = [key_prefix, func.__name__]
            key_parts.extend(str(a) for a in args[1:])
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            key = ":".join(key_parts)

            cached_value = await cache.get(key)
            if cached_value is not None:
                return cached_value

            result = await func(*args, **kwargs)
            await cache.set(key, result, ttl)
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            key_parts = [key_prefix, func.__name__]
            key_parts.extend(str(a) for a in args[1:])
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            key = ":".join(key_parts)

            return func(*args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator