"""Modelo que representa as materias da sala do aluno"""


from __future__ import annotations

from collections import defaultdict
from functools import cached_property
from typing import TYPE_CHECKING

from .mixins import SerializableMixin
from ..core.enums import Area

if TYPE_CHECKING:
    pass

__all__ = ("Materia", "agrupar_por_area")


_DISCIPLINE_DATA: dict[int, dict] = {
    1100: {
        "nome": "Língua Portuguesa",
        "sigla": "PORT",
        "emoji": "📚",
        "area": Area.LINGUAGENS,
    },
    1900: {
        "nome": "Educação Física",
        "sigla": "EDFIS",
        "emoji": "🏃",
        "area": Area.LINGUAGENS,
    },
    2100: {
        "nome": "Geografia",
        "sigla": "GEO",
        "emoji": "🌍",
        "area": Area.HUMANAS,
    },
    2200: {
        "nome": "História",
        "sigla": "HIST",
        "emoji": "📜",
        "area": Area.HUMANAS,
    },
    2300: {
        "nome": "Sociologia",
        "sigla": "SOC",
        "emoji": "👥",
        "area": Area.HUMANAS,
    },
    2400: {
        "nome": "Biologia",
        "sigla": "BIO",
        "emoji": "🧬",
        "area": Area.NATUREZA,
    },
    2600: {
        "nome": "Física",
        "sigla": "FIS",
        "emoji": "⚛️",
        "area": Area.NATUREZA,
    },
    2700: {
        "nome": "Matemática",
        "sigla": "MAT",
        "emoji": "🔢",
        "area": Area.MATEMATICA,
    },
    2800: {
        "nome": "Química",
        "sigla": "QUI",
        "emoji": "⚗️",
        "area": Area.NATUREZA,
    },
    8467: {
        "nome": "Língua Inglesa",
        "sigla": "ING",
        "emoji": "🔤",
        "area": Area.LINGUAGENS,
    },
    9929: {
        "nome": "Carreira e Competências",
        "sigla": "CCM",
        "emoji": "💼",
        "area": Area.OUTROS,
    },
    51000: {
        "nome": "Lógica e Programação",
        "sigla": "LLP",
        "emoji": "💻",
        "area": Area.TECNICO,
    },
    51002: {
        "nome": "Redes e Segurança",
        "sigla": "REDES",
        "emoji": "🌐",
        "area": Area.TECNICO,
    },
    51003: {
        "nome": "Processos de Desenvolvimento",
        "sigla": "PDS",
        "emoji": "🛠️",
        "area": Area.TECNICO,
    },
}


class Materia(SerializableMixin):
    """Representa uma matéria da escola.

    Attributes:
        codigo: Código da matéria
        nome: Nome da matéria
        abreviacao: Nome curtinho
        sigla: Sigla
        area: Área do conhecimento (BNCC)
        turma_id: ID da turma
    """

    __slots__ = (
        "codigo",
        "_nome_raw",
        "_abreviacao_raw",
        "turma_id",
        "numero_classe",
        "serie",
        "identificador",
        "escola_codigo",
        "escola_nome",
        "tipo_ensino",
        "turno",
        "situacao",
        "regular",
    )

    def __init__(self, *, data: dict) -> None:
        self.codigo = data["CodigoDisciplina"]
        self._nome_raw = data.get("NomeDisciplina", "")
        self._abreviacao_raw = data.get("NomeAbreviadoDisciplina", "")

        self.turma_id = data.get("CodigoTurma", 0)
        self.numero_classe = data.get("NumeroClasse", 0)
        self.serie = data.get("NumeroSerie", 0)
        self.identificador = data.get("IdentificadorTurma", "")

        self.escola_codigo = data.get("CodigoEscola", 0)
        self.escola_nome = data.get("NomeEscola", "")
        self.tipo_ensino = data.get("NomeTipoEnsino", "")
        self.turno = data.get("CodigoTurno", 0)

        self.situacao = data.get("Situacao", 0)
        self.regular = data.get("Regular", True)

    def __repr__(self) -> str:
        return f"<Materia {self.emoji} {self.nome!r} [{self.area.value}]>"

    def __str__(self) -> str:
        return self.nome

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Materia):
            return (
                self.codigo == other.codigo
                and self.turma_id == other.turma_id
            )
        return NotImplemented

    def __hash__(self) -> int:
        return hash((self.codigo, self.turma_id))

    @cached_property
    def nome(self) -> str:
        """Nome completo da matéria."""
        return _DISCIPLINE_DATA.get(self.codigo, {}).get(
            "nome", self._nome_raw.strip().title()
        )

    @cached_property
    def abreviacao(self) -> str:
        """Nome curto."""
        return self._abreviacao_raw.strip().title()

    @cached_property
    def sigla(self) -> str:
        """Sigla da matéria."""
        return _DISCIPLINE_DATA.get(self.codigo, {}).get(
            "sigla", self.abreviacao[:4].upper()
        )

    @cached_property
    def emoji(self) -> str:
        """Emoji que representa."""
        return _DISCIPLINE_DATA.get(self.codigo, {}).get("emoji", "📖")

    @cached_property
    def area(self) -> Area:
        """Área do saber (BNCC)."""
        data = _DISCIPLINE_DATA.get(self.codigo)
        if data:
            return data["area"]
        if self.is_tecnico:
            return Area.TECNICO
        return Area.OUTROS

    @property
    def is_tecnico(self) -> bool:
        """Diz se é matéria técnica/vocacional."""
        return self.codigo >= 50000

    @property
    def is_base_comum(self) -> bool:
        """Diz se é da base comum."""
        return self.area in (
            Area.LINGUAGENS,
            Area.HUMANAS,
            Area.NATUREZA,
            Area.MATEMATICA,
        )

    @property
    def is_diversificada(self) -> bool:
        """Diz se é componente diversificada."""
        return not self.is_base_comum and not self.is_tecnico

    @property
    def ativo(self) -> bool:
        """Diz se a matéria tá ativa."""
        return self.situacao == 0


def agrupar_por_area(materias: list[Materia]) -> dict[Area, list[Materia]]:
    """Agrupa matérias por área.

    Parâmetros:
        materias: lista de Materia

    Retorna:
        dicionário area -> lista de Materia
    """
    grupos: defaultdict[Area, list[Materia]] = defaultdict(list)
    for m in materias:
        grupos[m.area].append(m)
    return dict(sorted(grupos.items(), key=lambda x: x[0].value))