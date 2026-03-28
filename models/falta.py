"""
Representa uma falta de aluno. Não tem muita coisa, só os dados básicos mesmo, como data, disciplina, se foi justificada ou não, etc.
Também tem um modelo de ResumoFaltas que é um resumo de analise das faltas
"""


from __future__ import annotations

from datetime import datetime
from functools import cached_property
from typing import TYPE_CHECKING

from .mixins import SerializableMixin
from ..utils import format_relative_time

if TYPE_CHECKING:
    pass

__all__ = ("Falta", "ResumoFaltas")

LIMITE_DE_PRESENÇA = 0.75
AVISO_PRESENÇA_BUFFER = 0.10
TOTAL_ESTIMADO_DE_AULAS = 300


class Falta(SerializableMixin):
    """Representa uma falta de aluno

    Attributes:
        data: Data da falta
        data_fim: Data de término (para faltas de vários dias)
        dia_semana: Dia da semana
        disciplina_id: ID da disciplina
        quantidade: Número de aulas perdidas
        justificada: Mostra se a falta foi justificada
    """

    __slots__ = (
        "data",
        "data_fim",
        "dia_semana",
        "disciplina_id",
        "_nome_raw",
        "quantidade",
        "responsavel_ciente",
        "ciencia_id",
        "motivo_id",
        "anexos",
        "matricula_id",
        "data_solicitacao",
    )

    def __init__(self, *, data: dict) -> None:
        self.data = datetime.fromisoformat(data["dataAula"])
        self.data_fim = datetime.fromisoformat(data["dataAulaFim"])
        self.dia_semana = data.get("diaSemana", "")

        self.disciplina_id = data.get("disciplinaId", 0)
        self._nome_raw = data.get("nomeDisciplina", "")

        self.quantidade = data.get("quantidadeFaltas", 1)
        self.responsavel_ciente = data.get("flagResponsavelCiencia", False)
        self.ciencia_id = data.get("frequenciaResponsavelCienteId", 0)

        self.motivo_id = data.get("motivoId", 0)
        self.anexos = data.get("anexos", "")
        self.matricula_id = data.get("matriculaAlunoId", 0)

        _dt_solic = data.get("dataSolicitacao")
        self.data_solicitacao = (
            datetime.fromisoformat(_dt_solic) if _dt_solic else None
        )

    def __repr__(self) -> str:
        just = "✅" if self.justificada else "❌"
        return (
            f"<Falta {self.disciplina} x{self.quantidade} "
            f"em {self.data_formatada} just={just}>"
        )

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Falta):
            return (
                self.data == other.data
                and self.disciplina_id == other.disciplina_id
                and self.matricula_id == other.matricula_id
            )
        return NotImplemented

    def __hash__(self) -> int:
        return hash((self.data, self.disciplina_id, self.matricula_id))

    @cached_property
    def disciplina(self) -> str:
        """Nome da disciplina"""
        from .materia import _DISCIPLINE_DATA
        return _DISCIPLINE_DATA.get(self.disciplina_id, {}).get(
            "nome", self._nome_raw.strip().title()
        )

    @property
    def emoji(self) -> str:
        """Emoji da disciplina"""
        from .materia import _DISCIPLINE_DATA
        return _DISCIPLINE_DATA.get(self.disciplina_id, {}).get("emoji", "📚")

    @property
    def data_formatada(self) -> str:
        """Data formatada (DD/MM/YYYY)"""
        return self.data.strftime("%d/%m/%Y")

    @property
    def data_curta(self) -> str:
        """Data curta (DD/MM)"""
        return self.data.strftime("%d/%m")

    @property
    def tempo_atras(self) -> str:
        """String de tempo relativo"""
        return format_relative_time(self.data)

    @property
    def justificada(self) -> bool:
        """Verifica se a falta é justificada"""
        return self.motivo_id > 0

    @property
    def tem_anexo(self) -> bool:
        """Verifica se há anexos"""
        return bool(self.anexos.strip())

    @property
    def pendente_ciencia(self) -> bool:
        """Verifica se o responsável ainda não confirmou"""
        return not self.responsavel_ciente


class ResumoFaltas:
    """Resumo analítico de faltas

    Fornece estatísticas agregadas e insights sobre as faltas dos alunos
    """

    def __init__(self, faltas: list[Falta]) -> None:
        self._faltas = faltas
        # Precompute common aggregations
        self._total_aulas = sum(f.quantidade for f in faltas)
        self._total_justificadas = sum(
            f.quantidade for f in faltas if f.justificada
        )

    def __repr__(self) -> str:
        return (
            f"<ResumoFaltas total={self.total_aulas} "
            f"dias={self.dias_com_falta} "
            f"disciplinas={len(self.por_disciplina)}>"
        )

    @property
    def total_registros(self) -> int:
        """Total de registros de falta"""
        return len(self._faltas)

    @property
    def total_aulas(self) -> int:
        """Total de aulas perdidas"""
        return self._total_aulas

    @property
    def total_justificadas(self) -> int:
        """Total de faltas justificadas"""
        return self._total_justificadas

    @property
    def total_injustificadas(self) -> int:
        """Total de faltas não justificadas"""
        return self._total_aulas - self._total_justificadas

    @cached_property
    def por_disciplina(self) -> dict[str, int]:
        """Faltas agrupadas por disciplina"""

        quantidades: dict[str, int] = {}
        for f in self._faltas:
            quantidades[f.disciplina] = (
                quantidades.get(f.disciplina, 0) + f.quantidade
            )
        return dict(
            sorted(quantidades.items(), key=lambda x: x[1], reverse=True)
        )

    @cached_property
    def por_disciplina_id(self) -> dict[int, int]:
        """Faltas agrupadas por ID da disciplina"""
        quantidades: dict[int, int] = {}
        for f in self._faltas:
            quantidades[f.disciplina_id] = (
                quantidades.get(f.disciplina_id, 0) + f.quantidade
            )
        return quantidades

    @cached_property
    def por_data(self) -> dict[str, list[Falta]]:
        """Faltas agrupadas por data"""
        grupos: dict[str, list[Falta]] = {}
        for f in self._faltas:
            chave = f.data_formatada
            grupos.setdefault(chave, []).append(f)
        return dict(
            sorted(grupos.items(), key=lambda x: x[1][0].data, reverse=True)
        )

    @cached_property
    def por_dia_semana(self) -> dict[str, int]:
        """Faltas agrupadas por dia da semana"""
        grupos: dict[str, int] = {}
        for f in self._faltas:
            grupos[f.dia_semana] = grupos.get(f.dia_semana, 0) + f.quantidade
        return dict(sorted(grupos.items(), key=lambda x: x[1], reverse=True))

    @cached_property
    def por_mes(self) -> dict[str, int]:
        """Faltas agrupadas por mês"""
        meses: dict[str, int] = {}
        for f in self._faltas:
            chave = f.data.strftime("%m/%Y")
            meses[chave] = meses.get(chave, 0) + f.quantidade
        return dict(sorted(meses.items()))

    @property
    def disciplina_mais_faltas(self) -> str | None:
        """Disciplina com mais faltas"""
        por_disc = self.por_disciplina
        return next(iter(por_disc)) if por_disc else None

    @property
    def dia_mais_faltas(self) -> str | None:
        """Dia da semana com mais faltas"""
        por_dia = self.por_dia_semana
        return next(iter(por_dia)) if por_dia else None

    @property
    def dias_com_falta(self) -> int:
        """Número de dias únicos com falta"""
        return len({f.data.date() for f in self._faltas})

    @property
    def ultima_falta(self) -> Falta | None:
        """Última falta registrada"""
        return (
            max(self._faltas, key=lambda f: f.data) if self._faltas else None
        )

    @property
    def primeira_falta(self) -> Falta | None:
        """Primeira falta registrada"""
        return (
            min(self._faltas, key=lambda f: f.data) if self._faltas else None
        )

    def frequencia_estimada(self, total_aulas_previstas: int) -> float:
        """Calcula a taxa de presença estimada

        Args:
            total_aulas_previstas: Total de aulas previstas

        Returns:
            Taxa de presença (0.0 a 1.0)
        """
        if total_aulas_previstas <= 0:
            return 0.0
        presencas = total_aulas_previstas - self.total_aulas
        return max(0.0, presencas / total_aulas_previstas)

    def frequencia_percentual(self, total_aulas_previstas: int) -> int:
        """Calcula o percentual de presença"""
        return int(self.frequencia_estimada(total_aulas_previstas) * 100)

    @property
    def alerta_frequencia(self) -> bool:
        """Verifica se a presença está abaixo do limite"""
        return self.frequencia_estimada(TOTAL_ESTIMADO_DE_AULAS) < (
            LIMITE_DE_PRESENÇA + AVISO_PRESENÇA_BUFFER
        )