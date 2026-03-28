"""Outro modelo muito importante pq representa a turma da pessoa
   um modelo de Escola que tem alguns dados da escola.
   Não tem muita coisa sobre a Escola pois n encontrei uma api pra pegar os dados da Escola
   Só isso está bom.
   
   Sobre a Sala, tem varios dados só basta vc querer usar
"""


from __future__ import annotations

from datetime import datetime
from functools import cached_property
from typing import TYPE_CHECKING

from .mixins import APIAccessibleMixin, SerializableMixin
from ..core.cache import cached
from ..core.enums import Turno, SituacaoMatricula
from ..utils import encode_query

if TYPE_CHECKING:
    from ..core.state import ConnectionState

import re

_SERIES_SUFFIX_PATTERN = re.compile(
    r"(MANH|TARD|NOIT|ANUA)", re.IGNORECASE
)

if TYPE_CHECKING:
    from ..core.state import ConnectionState
    from .user import User
    from .materia import Materia
    from .task import Task
    from .essay import Essay

__all__ = ("Room", "Escola")


class Escola(SerializableMixin):
    """Representa uma escola."""

    __slots__ = ("codigo", "nome", "codigo_unidade")

    def __init__(
        self, *, codigo: int, nome: str, codigo_unidade: int
    ) -> None:
        self.codigo = codigo
        self.nome = nome
        self.codigo_unidade = codigo_unidade

    @property
    def nome_formatado(self) -> str:
        """Nome da escola formatado."""
        return self.nome.strip().title()

    def __repr__(self) -> str:
        return f"<Escola {self.nome!r}>"

    def __str__(self) -> str:
        return self.nome_formatado

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Escola):
            return self.codigo == other.codigo
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.codigo)


class Room(APIAccessibleMixin, SerializableMixin):
    """Representa uma turma.

    Attributes:
        id: ID da turma
        numero_classe: Número da classe
        identificador: Identificador da turma
        descricao: Descrição completa
        serie: Série
        ano_letivo: Ano letivo
        escola: Dados da escola
        turno: Turno
        situacao: Situação
    """

    __slots__ = (
        "id",
        "numero_classe",
        "identificador",
        "descricao",
        "numero_sala",
        "serie",
        "serie_aluno",
        "ano_letivo",
        "escola",
        "turno",
        "tipo_rede",
        "tipo_ensino_codigo",
        "tipo_ensino_nome",
        "situacao",
        "regular",
        "turma_mae",
        "inicio",
        "fim",
        "_state",
    )

    def __init__(self, *, data: dict, state: ConnectionState) -> None:
        self._bind_state(state)

        self.id = data["CodigoTurma"]
        self.numero_classe = data.get("NumeroClasse", 0)
        self.identificador = data.get("IdentificadorTurma", "")
        self.descricao = data.get("DescricaoTurma", "")
        self.numero_sala = data.get("NumeroSala", "")

        self.serie = data.get("NumeroSerie", 0)
        self.serie_aluno = data.get("NumeroSerieAluno", 0)
        self.ano_letivo = data.get("AnoLetivo", "")

        self.escola = Escola(
            codigo=data.get("CodigoEscola", 0),
            nome=data.get("NomeEscola", ""),
            codigo_unidade=data.get("CodigoUnidade", 0),
        )

        self.turno = Turno(data.get("CodigoTurno", 1))
        self.tipo_rede = data.get("TipoRedeEnsino", 0)
        self.tipo_ensino_codigo = data.get("CodigoTipoEnsino", 0)
        self.tipo_ensino_nome = data.get("NomeTipoEnsino", "")

        self.situacao = SituacaoMatricula(data.get("Situacao", 0))
        self.regular = data.get("Regular", True)
        self.turma_mae = data.get("CodigoTurmaMae", 0)

        self.inicio = datetime.fromisoformat(data["DataInicio"])
        self.fim = datetime.fromisoformat(data["DataFim"])

    def __repr__(self) -> str:
        return f"<Room {self.name!r} id={self.id}>"

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Room):
            return self.id == other.id
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.id)

    @cached_property
    def name(self) -> str:
        """Nome curto da turma."""
        return self._parse_nome_curto()

    @property
    def curso(self) -> str:
        """Nome do curso."""
        parts = self.descricao.split(" - ")
        if len(parts) >= 2:
            return parts[1].strip().title()
        return self.descricao.title()

    @property
    def turno_nome(self) -> str:
        """Nome do turno."""
        return str(self.turno)

    @property
    def situacao_nome(self) -> str:
        """Nome da situação."""
        return str(self.situacao)

    @property
    def ativo(self) -> bool:
        """Diz se a turma tá ativa."""
        now = datetime.now()
        return (
            self.situacao == SituacaoMatricula.ATIVO
            and self.inicio <= now <= self.fim
        )

    @property
    def em_andamento(self) -> bool:
        """Diz se o ano letivo tá rolando."""
        now = datetime.now()
        return self.inicio <= now <= self.fim

    @property
    def dias_restantes(self) -> int:
        """Dias restantes no ano letivo."""
        delta = self.fim - datetime.now()
        return max(0, delta.days)

    @property
    def progresso_ano(self) -> float:
        """Progresso do ano letivo (0.0 a 1.0)."""
        from ..utils import TimeUtil
        return TimeUtil.progress_ratio(datetime.now(), self.inicio, self.fim)

    @property
    def progresso_percentual(self) -> int:
        """Progresso do ano letivo em porcentagem."""
        return int(self.progresso_ano * 100)

    @property
    def is_tecnico(self) -> bool:
        """Diz se é curso técnico."""
        return "PROFISSIONAL" in self.tipo_ensino_nome.upper()

    @property
    def is_turma_filha(self) -> bool:
        """Diz se é turma filha."""
        return self.turma_mae > 0

    @property
    def serie_formatada(self) -> str:
        """Série formatada."""
        return f"{self.serie}ª Série"

    def _parse_nome_curto(self) -> str:
        """Pega o nome curto a partir da descrição."""
        parts = self.descricao.split(" - ")

        if len(parts) >= 3:
            curso = parts[1].strip().title()
            serie_raw = parts[2].strip()

            match = _SERIES_SUFFIX_PATTERN.search(serie_raw)
            if match:
                serie_raw = serie_raw[: match.start()]

            serie_limpa = (
                serie_raw.strip().replace("SERIE", "Série").title()
            )
            return f"{curso} - {serie_limpa}"

        if len(parts) >= 2:
            return parts[1].strip().title()

        return self.descricao.title()

    async def fetch_materias(self, user: User) -> list[Materia]:
        """Busca matérias dessa turma."""
        materias = await user.fetch_materias()
        return [m for m in materias if m.turma_id == self.id]

    async def _fetch_tasks(self, *, is_essay: bool = False) -> list[dict]:
        """Interno: busca dados brutos das tarefas."""
        from ..core.config import get_config

        config = get_config()

        params = {
            "expired_only": "false",
            "limit": 100,
            "offset": 0,
            "filter_expired": "true",
            "is_exam": "false",
            "with_answer": "true",
            "is_essay": str(is_essay).lower(),
            "answer_statuses": ["draft", "pending"],
            "with_apply_moment": "true",
            "publication_target": self._state.get_targets(self.name),
        }

        url = (
            f"{config.endpoints.EDUSP_BASE}/tms/task/todo?"
            f"{encode_query(params)}"
        )
        resp = await self._http.get(url)

        return (
            resp
            if isinstance(resp, list)
            else (resp or {}).get("tasks", [])
        )

    @cached(ttl=300, key_prefix="room")
    async def fetch_tasks(self) -> list[Task]:
        """Busca tarefas normais dessa turma."""
        from .task import Task

        raw = await self._fetch_tasks(is_essay=False)
        return [
            Task(data=t, room_name=self.name, state=self._state) for t in raw
        ]

    @cached(ttl=300, key_prefix="room")
    async def fetch_essays(self) -> list[Essay]:
        """Busca redações dessa turma."""
        from .essay import Essay

        raw = await self._fetch_tasks(is_essay=True)
        return [
            Essay(data=t, room_name=self.name, state=self._state)
            for t in raw
        ]