"""Representa a agenda de atividades
    Bom, tem os modelos de Aula, EventoEscolar, Avaliação e DiaAgenda que são os principais
    Dá pra fazer uma automação para avisar as suas aulas do dia e quando tem feriado ou eventos
    """

from __future__ import annotations

from datetime import datetime, date, time, timedelta
from functools import cached_property
from typing import TYPE_CHECKING

from collections import defaultdict
from .mixins import SerializableMixin
from ..core.enums import TipoEvento
from ..utils import format_relative_time, TimeUtil

if TYPE_CHECKING:
    pass

__all__ = (
    "Aula",
    "EventoEscolar",
    "Avaliacao",
    "DiaAgenda",
    "ResumoAvaliacoes",
)


class Aula(SerializableMixin):
    """Representa a Sala/Lição.

    Attributes:
        disciplina_id: int
        disciplina: str
        inicio: time
        fim: time
        dia_semana: str
    """

    __slots__ = (
        "aluno_id",
        "matricula_id",
        "escola_id",
        "turma_id",
        "descricao_turma",
        "ano_letivo",
        "disciplina_id",
        "_nome_raw",
        "dia_semana",
        "_hora_inicio",
        "_hora_fim",
    )

    def __init__(self, *, data: dict) -> None:
        self.aluno_id = data.get("alunoId", 0)
        self.matricula_id = data.get("matriculaAlunoId", 0)
        self.escola_id = data.get("escolaId", 0)
        self.turma_id = data.get("turmaId", 0)
        self.descricao_turma = data.get("descricaoTurma", "").strip()
        self.ano_letivo = data.get("anoLetivo", 0)

        self.disciplina_id = data.get("disciplinaId", 0)
        self._nome_raw = data.get("nomeDisciplina", "")

        self.dia_semana = data.get("diaDaSemana", 0)
        self._hora_inicio = data.get("horaInicioAula", "00:00:00")
        self._hora_fim = data.get("horaFimAula", "00:00:00")

    def __repr__(self) -> str:
        return f"<Aula {self.emoji} {self.horario} {self.disciplina!r}>"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Aula):
            return (
                self.disciplina_id == other.disciplina_id
                and self._hora_inicio == other._hora_inicio
                and self.dia_semana == other.dia_semana
            )
        return NotImplemented

    def __hash__(self) -> int:
        return hash((self.disciplina_id, self._hora_inicio, self.dia_semana))

    @cached_property
    def disciplina(self) -> str:
        """Nome"""
        if self.is_intervalo:
            return "Intervalo"
        from .materia import _DISCIPLINE_DATA
        return _DISCIPLINE_DATA.get(self.disciplina_id, {}).get(
            "nome", self._nome_raw
        )

    @property
    def emoji(self) -> str:
        """Emoji"""
        if self.is_intervalo:
            return "☕"
        from .materia import _DISCIPLINE_DATA
        return _DISCIPLINE_DATA.get(self.disciplina_id, {}).get("emoji", "📚")

    @cached_property
    def inicio(self) -> time:
        """Tempo inicial"""
        parts = self._hora_inicio.split(":")
        return time(int(parts[0]), int(parts[1]))

    @cached_property
    def fim(self) -> time:
        """Tempo final"""
        parts = self._hora_fim.split(":")
        return time(int(parts[0]), int(parts[1]))

    @property
    def inicio_fmt(self) -> str:
        """Tempo inicial formatado (HH:MM)."""
        return self.inicio.strftime("%H:%M")

    @property
    def fim_fmt(self) -> str:
        """Tempo final formatado (HH:MM)."""
        return self.fim.strftime("%H:%M")

    @property
    def horario(self) -> str:
        """Intervalo de tempo"""
        return f"{self.inicio_fmt} - {self.fim_fmt}"

    @property
    def duracao_minutos(self) -> int:
        """Duração em minutos"""
        dt_i = datetime.combine(date.today(), self.inicio)
        dt_f = datetime.combine(date.today(), self.fim)
        return int((dt_f - dt_i).total_seconds() / 60)

    @property
    def dia_semana_nome(self) -> str:
        """Nome do dia da semana"""
        dias = {
            1: "Segunda-feira",
            2: "Terça-feira",
            3: "Quarta-feira",
            4: "Quinta-feira",
            5: "Sexta-feira",
            6: "Sábado",
            7: "Domingo",
        }
        return dias.get(self.dia_semana, f"Dia {self.dia_semana}")

    @property
    def is_intervalo(self) -> bool:
        """Verifica se é intervalo"""
        return self.disciplina_id == -1

    @property
    def is_aula(self) -> bool:
        """Verifica se é a aula atual"""
        return not self.is_intervalo

    @property
    def em_andamento(self) -> bool:
        """Verifica se a aula está em andamento"""
        agora = datetime.now().time()
        return self.inicio <= agora <= self.fim

    @property
    def ja_passou(self) -> bool:
        """Verifica se a aula ja passou"""
        return datetime.now().time() > self.fim

    @property
    def ainda_nao_comecou(self) -> bool:
        """Verifica se a aula não começou"""
        return datetime.now().time() < self.inicio


class EventoEscolar(SerializableMixin):
    """Represents a school event.

    Attributes:
        descricao: Descrição do evento
        tipo: Tipo do Evento
        inicio: Inicio datetime
        fim: Fim datetime
        letivo: Seja um dia de aula ou não
    """

    __slots__ = (
        "escola_id",
        "ano_letivo",
        "letivo",
        "ativo",
        "descricao",
        "tipo",
        "inicio",
        "fim",
    )

    def __init__(self, *, data: dict) -> None:
        self.escola_id = data.get("escolaId", 0)
        self.ano_letivo = data.get("anoLetivo", 0)
        self.letivo = data.get("flagLetivo", False)
        self.ativo = data.get("flagAtivo", True)
        self.descricao = data.get("descricaoEvento", "").strip()
        self.tipo = data.get("descricaoTipoEvento", "").strip()
        self.inicio = datetime.fromisoformat(data["dataInicio"])
        self.fim = datetime.fromisoformat(data["dataFim"])

    def __repr__(self) -> str:
        return f"<EventoEscolar {self.emoji} {self.titulo!r} {self.periodo}>"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, EventoEscolar):
            return self.inicio == other.inicio and self.tipo == other.tipo
        return NotImplemented

    def __hash__(self) -> int:
        return hash((self.inicio, self.tipo))

    @property
    def emoji(self) -> str:
        """Evento emoji"""
        return TipoEvento.emoji

    @property
    def titulo(self) -> str:
        """Evento titulo"""
        return self.descricao or self.tipo.title()

    @property
    def tipo_formatado(self) -> str:
        """Tipo do evento formatado"""
        return self.tipo.strip().title()

    @property
    def inicio_fmt(self) -> str:
        """Data inicial formatado"""
        return self.inicio.strftime("%d/%m/%Y")

    @property
    def fim_fmt(self) -> str:
        """Data final formatado"""
        return self.fim.strftime("%d/%m/%Y")

    @property
    def periodo(self) -> str:
        """Data periodo em string"""
        if self.inicio.date() == self.fim.date():
            return self.inicio_fmt
        return f"{self.inicio_fmt} a {self.fim_fmt}"

    @property
    def duracao_dias(self) -> int:
        """Duração em dias"""
        return max(1, (self.fim - self.inicio).days + 1)

    @property
    def is_feriado(self) -> bool:
        """Verifica se é feriado"""
        return "FERIADO" in self.tipo.upper()

    @property
    def is_reposicao(self) -> bool:
        """Verifica se é reposição"""
        return "REPOSIÇÃO" in self.tipo.upper()

    @property
    def is_dia_nao_letivo(self) -> bool:
        """Verifica se não é dia letivo"""
        return "NÃO LETIVO" in self.tipo.upper()

    @property
    def em_andamento(self) -> bool:
        """Verifica se está em andamento"""
        return self.inicio <= datetime.now() <= self.fim

    @property
    def ja_passou(self) -> bool:
        """Verifica se já passou"""
        return datetime.now() > self.fim

    @property
    def dias_ate(self) -> int:
        """Verifica quantos dias falta"""
        return max(0, (self.inicio - datetime.now()).days)

    def contains_date(self, dt: date) -> bool:
        """Verifica se a data está dentro do período do evento"""
        return self.inicio.date() <= dt <= self.fim.date()


class Avaliacao(SerializableMixin):
    """Representa a grade de evolução

    Attributes:
        avaliacao_id: avaliação ID
        disciplina_id: disciplina ID
        bimestre: bimestre (1-4)
        data: Avaliação date
        descricao: Descrição
        peso: Peso
        nota: Nota (Se tiver)
    """

    __slots__ = (
        "nota_id",
        "avaliacao_id",
        "aluno_id",
        "turma_id",
        "disciplina_id",
        "bimestre",
        "data",
        "descricao",
        "tipo_atividade_id",
        "peso",
        "_nota_raw",
        "_data_exclusao",
    )

    def __init__(self, *, data: dict) -> None:
        self.nota_id = data.get("avaliacaoNotaId")
        self.avaliacao_id = data["avaliacaoId"]
        self.aluno_id = data.get("alunoId", 0)
        self.turma_id = data.get("codigoTurma", 0)

        self.disciplina_id = data.get("disciplinaId", 0)
        self.bimestre = data.get("bimestre", 0)

        self.data = datetime.fromisoformat(data["dataAvaliacao"])
        self.descricao = data.get("descricaoAvaliacao", "").strip()
        self.tipo_atividade_id = data.get("tipoAtividadeId", 0)

        self.peso = data.get("peso", 0.0) or 0.0
        self._nota_raw = data.get("notaAtribuida")
        self._data_exclusao = data.get("dataExclusao")

    def __repr__(self) -> str:
        return (
            f"<Avaliacao {self.emoji} {self.disciplina!r} "
            f"'{self.descricao}' nota={self.nota_formatada}>"
        )

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Avaliacao):
            return self.avaliacao_id == other.avaliacao_id
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.avaliacao_id)

    @cached_property
    def disciplina(self) -> str:
        """Nome"""
        from .materia import _DISCIPLINE_DATA
        return _DISCIPLINE_DATA.get(self.disciplina_id, {}).get(
            "nome", "Desconhecida"
        )

    @property
    def emoji(self) -> str:
        """Emoji."""
        from .materia import _DISCIPLINE_DATA
        return _DISCIPLINE_DATA.get(self.disciplina_id, {}).get("emoji", "📝")

    @property
    def nota(self) -> float | None:
        """Valor da Nota"""
        if self._nota_raw is not None:
            return float(self._nota_raw)
        return None

    @property
    def tem_nota(self) -> bool:
        """Verifica se tem nota"""
        return self.nota is not None

    @property
    def nota_formatada(self) -> str:
        """Nota formatada"""
        from ..utils import format_grade
        return format_grade(self.nota)

    @property
    def nota_ponderada(self) -> float | None:
        """Nota ponderada"""
        if self.nota is not None and self.peso > 0:
            return self.nota * self.peso / 100
        return None

    @property
    def pendente(self) -> bool:
        """Verifica se está pendente"""
        return not self.tem_nota and not self.excluida

    @property
    def excluida(self) -> bool:
        """Verifica se está excluida"""
        return self._data_exclusao is not None

    @property
    def data_formatada(self) -> str:
        """Formatted date."""
        return self.data.strftime("%d/%m/%Y")

    @property
    def data_curta(self) -> str:
        """Data formatada (curta)"""
        return self.data.strftime("%d/%m")

    @property
    def bimestre_fmt(self) -> str:
        """Bimestre formatado"""
        return f"{self.bimestre}º Bim"


class DiaAgenda:
    """Representa os dias da agenda

    Attributes:
        data: data
        aulas: lista as aulas
        eventos: lista os eventos
    """

    _DIAS_SEMANA = {
        0: "Segunda-feira",
        1: "Terça-feira",
        2: "Quarta-feira",
        3: "Quinta-feira",
        4: "Sexta-feira",
        5: "Sábado",
        6: "Domingo",
    }

    def __init__(
        self,
        *,
        date: date,
        aulas: list[Aula],
        eventos: list[EventoEscolar] | None = None,
    ) -> None:
        self.data = date
        self.aulas = sorted(aulas, key=lambda a: a.inicio)
        self.eventos = eventos or []

        self._aulas_reais = [a for a in self.aulas if a.is_aula]

    def __repr__(self) -> str:
        return (
            f"<DiaAgenda {self.data_formatada} ({self.dia_semana}) "
            f"{self.total_aulas} aulas>"
        )

    @property
    def data_formatada(self) -> str:
        """Data formatada"""
        return self.data.strftime("%d/%m/%Y")

    @property
    def dia_semana(self) -> str:
        """Dia da semana"""
        return self._DIAS_SEMANA.get(self.data.weekday(), "")

    @property
    def is_hoje(self) -> bool:
        """Verifica se é hj"""
        return self.data == date.today()

    @property
    def total_aulas(self) -> int:
        """Quantidade de aulas"""
        return len(self._aulas_reais)

    @cached_property
    def disciplinas(self) -> list[str]:
        """Lista todas as disciplinas"""
        seen: set[str] = set()
        result: list[str] = []
        for a in self._aulas_reais:
            if a.disciplina not in seen:
                seen.add(a.disciplina)
                result.append(a.disciplina)
        return result

    @property
    def inicio(self) -> time | None:
        """Horario do inicio da primeira aula (time)"""
        return self._aulas_reais[0].inicio if self._aulas_reais else None

    @property
    def fim(self) -> time | None:
        """Fim da ultima aula (time)"""
        return self._aulas_reais[-1].fim if self._aulas_reais else None

    @property
    def periodo(self) -> str:
        """Horário das aulas"""
        if self.inicio and self.fim:
            return (
                f"{self.inicio.strftime('%H:%M')} - {self.fim.strftime('%H:%M')}"
            )
        return ""

    @property
    def tem_evento(self) -> bool:
        """Verifica se tem evento no dia"""
        return bool(self.eventos)

    @property
    def is_feriado(self) -> bool:
        """Verifica se tem feriado"""
        return any(e.is_feriado for e in self.eventos)

    @property
    def aula_atual(self) -> Aula | None:
        """Retorna a aula atual"""
        if not self.is_hoje:
            return None
        now = datetime.now().time()
        for a in self.aulas:
            if a.inicio <= now <= a.fim:
                return a
        return None

    @property
    def proxima_aula(self) -> Aula | None:
        """Retonar a proxima aula"""
        if not self.is_hoje:
            return None
        now = datetime.now().time()
        for a in self._aulas_reais:
            if now < a.inicio:
                return a
        return None


class ResumoAvaliacoes:
    """Resumo das Availiações"""

    def __init__(self, avaliacoes: list[Avaliacao]) -> None:
        self._avaliacoes = [a for a in avaliacoes if not a.excluida]

    def __repr__(self) -> str:
        return (
            f"<ResumoAvaliacoes total={self.total} "
            f"com_nota={len(self.com_nota)} pendentes={len(self.pendentes)}>"
        )

    @property
    def total(self) -> int:
        """Total de avaliações"""
        return len(self._avaliacoes)

    @property
    def com_nota(self) -> list[Avaliacao]:
        """Avaliações com nota"""
        return [a for a in self._avaliacoes if a.tem_nota]

    @property
    def pendentes(self) -> list[Avaliacao]:
        """Avaliação pendentes"""
        return [a for a in self._avaliacoes if a.pendente]

    @cached_property
    def por_bimestre(self) -> dict[int, list[Avaliacao]]:
        """Agrupa por bimestre"""
        grupos: defaultdict[int, list[Avaliacao]] = defaultdict(list)
        for a in self._avaliacoes:
            grupos[a.bimestre].append(a)
        return dict(sorted(grupos.items()))

    @cached_property
    def por_disciplina(self) -> dict[str, list[Avaliacao]]:
        """Agrupa por disciplina"""
        grupos: defaultdict[str, list[Avaliacao]] = defaultdict(list)
        for a in self._avaliacoes:
            grupos[a.disciplina].append(a)
        return dict(sorted(grupos.items()))

    @cached_property
    def _medias_cache(self) -> dict[int, float]:
        """Cache para medias de disciplinas"""
        from .materia import _DISCIPLINE_DATA

        disc_ids = {a.disciplina_id for a in self._avaliacoes if a.tem_nota}
        medias: dict[int, float] = {}

        for did in disc_ids:
            avals = [
                a
                for a in self._avaliacoes
                if a.disciplina_id == did and a.tem_nota
            ]
            if not avals:
                continue

            soma_pond = sum(a.nota * a.peso for a in avals)
            soma_pesos = sum(a.peso for a in avals)

            if soma_pesos > 0:
                medias[did] = soma_pond / soma_pesos

        return medias

    def media_disciplina(self, disciplina_id: int) -> float | None:
        """Calcular a média ponderada de uma disciplina"""
        return self._medias_cache.get(disciplina_id)

    def media_disciplina_fmt(self, disciplina_id: int) -> str:
        """Média formatada para uma disciplina"""
        from ..utils import format_grade
        return format_grade(self.media_disciplina(disciplina_id))

    @cached_property
    def medias_gerais(self) -> dict[str, float]:
        """Médias de todas as disciplinas"""
        from .materia import _DISCIPLINE_DATA

        medias: dict[str, float] = {}

        for did, media in self._medias_cache.items():
            nome = _DISCIPLINE_DATA.get(did, {}).get(
                "nome", f"Disciplina {did}"
            )
            medias[nome] = round(media, 1)

        return dict(sorted(medias.items(), key=lambda x: x[1], reverse=True))