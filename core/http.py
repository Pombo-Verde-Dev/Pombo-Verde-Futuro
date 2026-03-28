"""
Simplesmente o sistema mais dificil que eu ja fiz na minha vida kkkkkk
No ano passado eu comecei esse http.py copiando a logica do codigo fonte do discord.py
depois fui editando e editando até chegar nisso, e ainda tem muita coisa pra melhorar
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, TYPE_CHECKING

import aiohttp
from aiohttp import ClientResponse, ClientError, ClientTimeout

from .errors import (
    APIError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ForbiddenError,
)
from .config import get_config

if TYPE_CHECKING:
    from ..client import Client

__all__ = ("HTTPClient",)

logger = logging.getLogger(__name__)


class HTTPClient:
    """Cliente HTTP assíncrono com suporte a retries, rate limits e erros personalizados."""
    def __init__(
        self,
        headers: dict[str, str] | None = None,
        timeout: int | None = None,
        max_retries: int | None = None,
    ) -> None:
        config = get_config()

        self._headers = headers or config.HEADERS.copy()
        self._timeout = ClientTimeout(total=timeout or config.DEFAULT_TIMEOUT)
        self._max_retries = max_retries or config.MAX_RETRIES
        self._backoff_factor = config.BACKOFF_FACTOR
        self._session: aiohttp.ClientSession | None = None
        self._closed = True

    @property
    def is_closed(self) -> bool:
        """Verifica se a sessão está fechada"""
        return self._closed or self._session is None or self._session.closed

    async def __aenter__(self) -> HTTPClient:
        """Abre a sessão ao iniciar o with"""
        await self.open()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Fecha a sessão ao sair do with"""
        await self.close()

    async def open(self) -> None:
        """Abre a sessão se não estiver aberta"""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=30,
                enable_cleanup_closed=True,
                force_close=False,
            )
            self._session = aiohttp.ClientSession(
                headers=self._headers,
                timeout=self._timeout,
                connector=connector,
                raise_for_status=False,
            )
            self._closed = False
            logger.debug("HTTP session opened")

    async def close(self) -> None:
        """Fecha a sessão se estiver aberta"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._closed = True
            logger.debug("HTTP session closed")

    def set_token(self, token: str) -> None:
        """Defini o token para autenticar nas requisições"""
        self._headers["x-api-key"] = token
        if self._session and not self._session.closed:
            self._session._default_headers["x-api-key"] = token

    def set_header(self, key: str, value: str) -> None:
        """Defini um header personalizado para as requisições"""
        self._headers[key] = value
        if self._session and not self._session.closed:
            self._session._default_headers[key] = value

    async def request(
        self,
        method: str,
        url: str,
        *,
        max_retries: int | None = None,
        **kwargs: Any,
    ) -> Any:
        """Faz requisições na url com metodo especificado com tratamentos de erros, retries e rate limits.
        
        Parâmetros:
            method: método HTTP (GET, POST, etc)
            url: URL da requisição
            max_retries: número máximo de tentativas (opcional, padrão é o configurado)
            **kwargs: argumentos adicionais para aiohttp (json, headers, etc)
        """
        if self.is_closed:
            await self.open()

        max_retries = max_retries or self._max_retries
        last_exception: Exception | None = None

        for attempt in range(1, max_retries + 1):
            try:
                logger.debug(
                    f"[{method}] {url} (attempt {attempt}/{max_retries})"
                )

                async with self._session.request(method, url, **kwargs) as response:
                    return await self._handle_response(response, method, url)

            except asyncio.TimeoutError as exc:
                logger.warning(f"Timeout on {url} (attempt {attempt})")
                last_exception = exc

            except ClientError as exc:
                logger.warning(f"Client error on {url}: {exc}")
                last_exception = exc

            if attempt < max_retries:
                wait = self._backoff_factor ** attempt
                logger.debug(f"Retrying in {wait:.2f} seconds...")
                await asyncio.sleep(wait)

        raise APIError(
            f"Failed after {max_retries} attempts",
            url=url,
            method=method,
        ) from last_exception

    async def _handle_response(
        self,
        response: ClientResponse,
        method: str,
        url: str,
    ) -> Any:
        if response.status == 429:
            retry_after = float(response.headers.get("Retry-After", 5))
            raise RateLimitError(retry_after, url=url, method=method)

        if response.status == 401:
            raise AuthenticationError("Invalid or expired token")

        if response.status == 403:
            raise ForbiddenError(url=url)

        if response.status == 404:
            raise NotFoundError("Resource", url=url)

        if response.status >= 500:
            response.raise_for_status()

        if response.status >= 400:
            text = await response.text()
            raise APIError(
                text,
                status_code=response.status,
                url=url,
                method=method,
            )

        if response.status == 204 or not response.content:
            return None

        try:
            return await response.json()
        except ValueError:
            return await response.text()

    async def get(self, url: str, **kwargs: Any) -> Any:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> Any:
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs: Any) -> Any:
        return await self.request("PUT", url, **kwargs)

    async def patch(self, url: str, **kwargs: Any) -> Any:
        return await self.request("PATCH", url, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> Any:
        return await self.request("DELETE", url, **kwargs)