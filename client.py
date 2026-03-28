"""Não tem oq falar né.
Client principal para se comunicar com a api da sala do futuro
Simula as ações do usuario como login  pegar notificações DADOS SIMPLES do usuario
Simplesmente o melhor sistema que ja fiz para se comunicar com uma api. 
inspirado na estrutura do Discord.py de Rapptz, que é a melhor estrutura de client que eu já vi.
fácil de usar, intuitiva e eficiente

Futuramente pretendo adicionar muita funcionalidades de automação com a gemini
permitir fazer provas, tarefas, redações
Detectar Eventos sem abusar da Api e ficar obv que é um bot

Quem que ler esses arquivos, se souber um jeito de fazer isso (detectar Eventos)
Pois a sala do futuro não tem um websocket que atualiza os dados da pagina dinamicamente
então a unica maneira de detectar novos eventos é fazendo polling na api
o que é ruim pois pode ser detectado facilmente como um bot

Mas pretendo fazer um on_ready, on_task_posted, on_essay_posted events e vai indo
Já tenho uma base que seria tipo:

>>> client = Client(ra="1234567890123", uf="SP", senha="admin123", gemini_key="sua-chave-gemini-aqui")
>>> await client.login()
>>> @client.event
>>> async def on_ready():
>>>     print(f"Client pronto! Logado como {client.user.name}")

"""

from __future__ import annotations

import re
import asyncio
import logging
from typing import Any, Callable, Coroutine, TYPE_CHECKING

from .core import HTTPClient, ConnectionState, get_config, Config
from .models import User
from .core.errors import AuthenticationError, ValidationError
from .core.enums import UF
from .generator import Generator

if TYPE_CHECKING:
    from .models import Room, Notificacao, Aviso, Feed

__all__ = ("Client",)

logger = logging.getLogger(__name__)


class Client:
    """Client principal para se comunicar com a api da Sala do futuro.
    
       Inspirado na estrutura do Discord.py de Rapptz.
       
       Example:
            >>> from salafuturo import sf
            >>> async def main() -> None:
            >>>     async with sf.Client(ra="1234567890123", uf="SP", senha="admin123") as client:
            >>>       
            >>>         await client.login()
            >>>
            >>>         user = client.user
            >>>         print(f"Entrei na conta de: {user.name}")   
            >>> asyncio.run(main()) 
    """

    def __init__(
        self,
        *,
        ra: str,
        uf: str | UF,
        senha: str,
        gemini_key: str | None = None,
        config: Config | None = None,
    ) -> None:
        """Iniciar o Client

        Args:
            ra: RA do aluno (13 digitos)
            uf: Estado ex: (SP, RJ, etc)
            senha: Senha
            gemini_key: Chave de api para Gemini. Opcional
            config: Configuração customizada. Opcional
        """
        cleaned = re.sub(r"[\.\- ]", "", ra)
        if len(cleaned) != 13 or not cleaned.isdigit():
            raise ValidationError(
                "ra",
                f"O RA precisa ter 13 digitos: {ra!r}",
            )

        self._ra = cleaned
        self._uf = UF(uf.upper()) if isinstance(uf, str) else uf
        self._senha = senha
        self._gemini_key = gemini_key

        if config:
            from .core import set_config
            set_config(config)

        self._http: HTTPClient | None = None
        self._user: User | None = None
        self._state: ConnectionState | None = None
        self._closed = True


    @property
    def user(self) -> User:
        """Pega o usuario autenticado

        Raises:
            AuthenticationError: Se não estiver registrado
        """
        if self._user is None:
            raise AuthenticationError("Usuario não registrado. Chame o Login primeiro")
        return self._user

    @property
    def is_logged_in(self) -> bool:
        """Verifica se registrado"""
        return self._user is not None

    @property
    def is_closed(self) -> bool:
        """Verifica se o client desconectou"""
        return self._closed

    async def __aenter__(self) -> Client:
        await self.login()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()


    async def login(self) -> User:
        """Autentica e inicializa a sessão

        Returns:
            Autenticado User

        Raises:
            AuthenticationError: Se o credenciais estiver errados
        """
        logger.info(f"Conectado com RA={self._ra} UF={self._uf.value}")

        sed_token = await self._login_sed()

        await self._cabiar_token(sed_token)

        logger.info(f"Sucesso ao conectar com {self._user}")
        return self._user

    async def _login_sed(self) -> str:
        """Conecta com o login da sed"""
        config = get_config()

        async with HTTPClient({
            **config.HEADERS,
            "Ocp-Apim-Subscription-Key": config.SUBSCRIPTION_KEY,
        }) as http:
            resp = await http.post(
                f"{config.endpoints.SED_BASE}saladofuturobffapi/credenciais/api/LoginCompletoToken",
                json={
                    "user": f"{self._ra}{self._uf.value}",
                    "senha": self._senha,
                },
            )

        if not resp or "token" not in resp:
            raise AuthenticationError("Invalid credentials or SED API error")

        # Guarda os dados do usuario temporiamente 
        dados = resp.get("DadosUsuario", {})
        self._pending_user_data = {
            "name": dados.get("NAME", "Unknown"),
            "username": dados.get("NM_NICK", "Unknown"),
            "id": int(dados.get("CD_USUARIO", 0)),
            "email": dados.get("EMAIL", ""),
            "email_google": dados.get("EMAIL_GOOGLE", ""),
            "email_ms": dados.get("EMAIL_MS", ""),
        }

        return resp["token"]

    async def _cabiar_token(self, sed_token: str) -> None:
        """Cabiar SED token para EDUSP token."""
        config = get_config()

        self._http = HTTPClient(config.HEADERS)
        await self._http.open()

        resp = await self._http.post(
            f"{config.endpoints.EDUSP_BASE}/registration/edusp/token",
            json={"token": sed_token},
        )

        if not resp or "auth_token" not in resp:
            await self._http.close()
            raise AuthenticationError("Failed to exchange token")

        auth_token = resp["auth_token"]
        self._http.set_token(auth_token)

        # Criar o Estado e o usuario
        generator = Generator(self._gemini_key) if self._gemini_key else None

        self._state = ConnectionState(
            http=self._http,
            user=None,
            token=sed_token,
            generator=generator,
        )

        self._user = User(
            **self._pending_user_data,
            state=self._state,
            token=sed_token,
        )

        # Atualizar o estado com o usuario 
        self._state.user = self._user
        self._closed = False

    async def close(self) -> None:
        """Saia do client e limpe os dados"""
        if self._closed:
            return

        if self._state:
            await self._state.close()

        self._user = None
        self._state = None
        self._http = None
        self._closed = True

        logger.debug("Client desligado")

    async def fetch_rooms(self) -> list[Room]:
        """Obter a Sala do usuario"""
        return await self.user.fetch_rooms()

    async def fetch_notifications(self) -> list[Notificacao]:
        """Obter as notificações do usuario"""
        return await self.user.fetch_notifications()

    async def fetch_feed(self, room_id: int) -> Feed:
        """Obtter as notificações do mural do usuario"""
        return await self.user.fetch_feed(room_id)

    def __repr__(self) -> str:
        status = "logged_in" if self.is_logged_in else "not_logged_in"
        return f"<Client ra={self._ra!r} uf={self._uf.value!r} status={status}>"