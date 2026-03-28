"""Bom, o modelo principal do codigo, 
representa o usuário logado e tem métodos pra buscar as coisas mais comuns como turmas, 
matérias, faltas, avaliações, mural e notificações. 
Ele é o ponto de partida pra quase tudo que o código faz, então tem bastante coisa aqui.
"""

from __future__ import annotations

from datetime import date, timedelta
from functools import cached_property
from typing import TYPE_CHECKING, Any
import asyncio

from .mixins import APIAccessibleMixin, SerializableMixin
from ..core.cache import cached
from ..utils import encode_query
from ..core.enums import UF

if TYPE_CHECKING:
    from ..core.state import ConnectionState
    from .room import Room
    from .materia import Materia
    from .falta import Falta, ResumoFaltas
    from .agenda import (
        DiaAgenda,
        EventoEscolar,
        Avaliacao,
        ResumoAvaliacoes,
    )
    from .mural import Aviso
    from .notification import Notificacao
    from .feed import Feed

__all__ = ("User",)


class User(APIAccessibleMixin, SerializableMixin):
    """Representa um usuário da Sala do Futuro.

    Attributes:
        id: ID do usuário
        name: Nome completo
        username: Apelido
        email: Email principal
        email_google: Email Google
        email_ms: Email Microsoft
    """

    __slots__ = (
        "id",
        "name",
        "username",
        "email",
        "email_google",
        "email_ms",
        "_state",
        "_token",
    )

    def __init__(
        self,
        *,
        id: int,
        name: str,
        username: str,
        email: str,
        email_google: str,
        email_ms: str,
        state: ConnectionState,
        token: str,
    ) -> None:
        self.id = id
        self.name = name
        self.username = username
        self.email = email
        self.email_google = email_google
        self.email_ms = email_ms
        self._state = state
        self._token = token

    @cached_property
    def _codigo_aluno(self) -> str:
        """Código do aluno (tirado do ID)."""
        sid = str(self.id)
        return sid[:-1] if len(sid) > 1 else sid

    def __repr__(self) -> str:
        return f"<User id={self.id} name={self.name!r}>"

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other: object) -> bool:
        if isinstance(other, User):
            return self.id == other.id
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.id)

    def _sed_headers(
        self, subscription_key: str | None = None
    ) -> dict[str, str]:
        """Gera cabeçalhos pra API SED."""
        from ..core.config import get_config

        config = get_config()
        return {
            "Authorization": f"Bearer {self._token}",
            "Ocp-Apim-Subscription-Key": subscription_key
            or config.SUBSCRIPTION_KEY,
        }

    async def _sed_get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        subscription_key: str | None = None,
    ) -> Any:
        """Faz requisição GET autenticada pro SED."""
        from ..core.config import get_config

        config = get_config()
        url = f"{config.endpoints.SED_BASE}{path}"

        return await self._http.get(
            url,
            params=params,
            headers=self._sed_headers(subscription_key),
        )

    @staticmethod
    def _unwrap_response(resp: Any, *, key: str = "data") -> list[dict]:
        """Desembrulha resposta da API SED."""
        if not resp or not resp.get("isSucess"):
            return []
        payload = resp.get(key)
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            return [payload]
        return []

    @cached(ttl=300, key_prefix="user")
    async def fetch_rooms(self) -> list[Room]:
        """Busca as turmas do usuário.

        Retorna:
            Lista de Room
        """
        from .room import Room

        resp = await self._sed_get(
            "saladofuturobffapi/apihubintegracoes/api/v2/Turma/ListarTurmasPorAluno",
            params={"codigoAluno": self._codigo_aluno},
        )
        return [
            Room(data=item, state=self._state)
            for item in self._unwrap_response(resp)
        ]

    @cached(ttl=180, key_prefix="user")
    async def fetch_notifications(self) -> list[Notificacao]:
        """Busca notificações do usuário.

        Retorna:
            Lista de Notificacao
        """
        from .notification import Notificacao
        from ..core.config import get_config

        config = get_config()

        resp = await self._http.get(
            f"{config.endpoints.cmsp_api}api/sala-do-futuro-alunos/consulta-notificacao-cmsp",
            params={"userId": self.id},
            headers={
                "Ocp-Apim-Subscription-Key": config.SUBSCRIPTION_KEY2
            },
        )

        if not resp:
            return []

        items = (
            resp
            if isinstance(resp, list)
            else resp.get("notifications", [])
        )
        return [
            Notificacao(data=item, state=self._state) for item in items
        ]

    @cached(ttl=120, key_prefix="user")
    async def fetch_mural(
        self, room_id: int, profile: int = 1
    ) -> list[Aviso]:
        """Busca avisos do mural de uma turma.

        Parâmetros:
            room_id: ID da turma
            profile: Filtro de perfil (1=Professor, 4=Gestão)

        Retorna:
            Lista de Aviso
        """
        from .mural import Aviso
        from ..core.config import get_config

        config = get_config()

        resp = await self._http.get(
            f"{config.endpoints.mural_api}api/mural-avisos/listar-avisos-turma",
            params={
                "CodigoUsuario": self.id,
                "PerfilAviso": profile,
                "Turmas": room_id,
            },
            headers={
                "Ocp-Apim-Subscription-Key": config.SUBSCRIPTION_KEY3
            },
        )

        if not resp or not resp.get("success"):
            return []

        return [
            Aviso(data=item, state=self._state)
            for item in resp.get("data", [])
        ]

    async def fetch_feed(self, room_id: int) -> Feed:
        """Junta notificações e mural num feed só.

        Parâmetros:
            room_id: ID da turma

        Retorna:
            Feed com notificações e avisos
        """
        from .feed import Feed

        notifications, mural = await asyncio.gather(
            self.fetch_notifications(),
            self.fetch_mural(room_id),
            return_exceptions=True,
        )

        if isinstance(notifications, Exception):
            notifications = []
        if isinstance(mural, Exception):
            mural = []

        feed = Feed()
        feed.add_items(*notifications, *mural)
        return feed

    @cached(ttl=600, key_prefix="user")
    async def fetch_materias(self) -> list[Materia]:
        """Busca as disciplinas do usuário.

        Retorna:
            Lista de Materia
        """
        from .materia import Materia

        resp = await self._sed_get(
            "saladofuturobffapi/apihubintegracoes/api/v2/Disciplina/ListarDisciplinaPorAluno",
            params={"codigoAluno": self._codigo_aluno},
        )
        return [
            Materia(data=item) for item in self._unwrap_response(resp)
        ]

    @cached(ttl=300, key_prefix="user")
    async def fetch_faltas(self, year: int | None = None) -> list[Falta]:
        """Busca as faltas do usuário.

        Parâmetros:
            year: Ano letivo (padrão: ano atual)

        Retorna:
            Lista de Falta
        """
        from .falta import Falta

        year = year or date.today().year

        resp = await self._sed_get(
            "saladofuturobffapi/apiboletim/api/Frequencia/GetAlunoUltimosDiasFalta",
            params={
                "codigoAluno": self._codigo_aluno,
                "anoLetivo": year,
            },
        )
        return [
            Falta(data=item) for item in self._unwrap_response(resp)
        ]

    async def fetch_resumo_faltas(
        self, year: int | None = None
    ) -> ResumoFaltas:
        """Busca resumo das faltas.

        Retorna:
            ResumoFaltas com análises
        """
        from .falta import ResumoFaltas

        faltas = await self.fetch_faltas(year)
        return ResumoFaltas(faltas)

    async def fetch_agenda_dia(
        self, dt: date | None = None
    ) -> DiaAgenda:
        """Busca a agenda de um dia específico.

        Parâmetros:
            dt: Data pra buscar (padrão: hoje)

        Retorna:
            DiaAgenda da data
        """
        from .agenda import DiaAgenda, Aula

        dt = dt or date.today()

        resp = await self._sed_get(
            "saladofuturobffapi/apiboletim/api/Agenda/GetAgendaDia",
            params={
                "codigoAluno": self._codigo_aluno,
                "anoLetivo": dt.year,
                "dataAgenda": dt.isoformat(),
            },
        )

        raw = self._unwrap_response(resp)
        data = raw[0] if raw else {}
        aulas = [Aula(data=item) for item in data.get("agendaAluno", [])]

        return DiaAgenda(date=dt, aulas=aulas)

    async def fetch_eventos(
        self,
        start: date | None = None,
        end: date | None = None,
    ) -> list[EventoEscolar]:
        """Busca os eventos escolares num intervalo.

        Parâmetros:
            start: Data inicial (padrão: hoje)
            end: Data final (padrão: 30 dias depois)

        Retorna:
            Lista de EventoEscolar
        """
        from .agenda import EventoEscolar

        start = start or date.today()
        end = end or (start + timedelta(days=30))

        resp = await self._sed_get(
            "saladofuturobffapi/apiboletim/api/Agenda/GetAgendaPeriodoEscola",
            params={
                "codigoAluno": self._codigo_aluno,
                "anoLetivo": start.year,
                "dataInicio": start.isoformat(),
                "dataFim": end.isoformat(),
            },
        )
        return [
            EventoEscolar(data=item)
            for item in self._unwrap_response(resp)
        ]

    async def fetch_agenda_semana(
        self, start: date | None = None
    ) -> list[DiaAgenda]:
        """Busca a agenda semanal (seg-sex)."""
        start = start or date.today()
        start -= timedelta(days=start.weekday())

        events = await self.fetch_eventos(
            start, start + timedelta(days=6)
        )

        dias = []
        for offset in range(5):
            dt = start + timedelta(days=offset)
            dia = await self.fetch_agenda_dia(dt)
            dia.eventos = [e for e in events if e.contains_date(dt)]
            dias.append(dia)

        return dias

    @cached(ttl=600, key_prefix="user")
    async def fetch_avaliacoes(
        self, year: int | None = None
    ) -> list[Avaliacao]:
        """Busca todas as notas/avaliações.

        Parâmetros:
            year: Ano letivo (padrão: ano atual)

        Retorna:
            Lista de Avaliacao
        """
        from .agenda import Avaliacao

        year = year or date.today().year

        resp = await self._sed_get(
            "saladofuturobffapi/apiboletim/api/Avaliacao/GetAvaliacaoAluno",
            params={
                "AlunoId": self._codigo_aluno,
                "AnoLetivo": year,
            },
        )
        return [
            Avaliacao(data=item)
            for item in self._unwrap_response(resp)
        ]

    async def fetch_resumo_avaliacoes(
        self, year: int | None = None
    ) -> ResumoAvaliacoes:
        """Busca resumo das avaliações.

        Retorna:
            ResumoAvaliacoes com análises
        """
        from .agenda import ResumoAvaliacoes

        avaliacoes = await self.fetch_avaliacoes(year)
        return ResumoAvaliacoes(avaliacoes)