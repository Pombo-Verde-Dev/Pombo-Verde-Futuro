from __future__ import annotations

from enum import Enum, IntEnum

__all__ = (
    "UF",
    "Categoria",
    "Prioridade",
    "TipoAcao",
    "Area",
    "Turno",
    "SituacaoMatricula",
    "TipoEvento",
    "PerfilAviso",
    "StatusTarefa",
    "TipoAtividade",
)


class UF(str, Enum):
    AC = "AC"
    AL = "AL"
    AP = "AP"
    AM = "AM"
    BA = "BA"
    CE = "CE"
    DF = "DF"
    ES = "ES"
    GO = "GO"
    MA = "MA"
    MT = "MT"
    MS = "MS"
    MG = "MG"
    PA = "PA"
    PB = "PB"
    PR = "PR"
    PE = "PE"
    PI = "PI"
    RJ = "RJ"
    RN = "RN"
    RS = "RS"
    RO = "RO"
    RR = "RR"
    SC = "SC"
    SP = "SP"
    SE = "SE"
    TO = "TO"


class Categoria(str, Enum):
    ESTAGIO = "estagio"
    OLIMPIADA = "olimpiada"
    MONITOR = "monitor"
    WEBSERIE = "webserie"
    COPA = "copa"
    CURSO = "curso"
    OUTRO = "outro"


class Prioridade(str, Enum):
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    URGENTE = "urgente"


class TipoAcao(str, Enum):
    INSCRICAO = "inscricao"
    ASSISTIR = "assistir"
    ACESSAR = "acessar"
    INFORMATIVO = "informativo"


class Area(str, Enum):
    LINGUAGENS = "Linguagens"
    HUMANAS = "Ciências Humanas"
    NATUREZA = "Ciências da Natureza"
    MATEMATICA = "Matemática"
    TECNICO = "Técnico"
    OUTROS = "Outros"


class Turno(IntEnum):
    MANHA = 1
    TARDE = 2
    NOITE = 3
    INTEGRAL = 4

    def __str__(self) -> str:
        names = {
            1: "Manhã",
            2: "Tarde",
            3: "Noite",
            4: "Integral",
        }
        return names.get(self.value, f"Turno {self.value}")


class SituacaoMatricula(IntEnum):
    ATIVO = 0
    TRANSFERIDO = 1
    DESISTENTE = 2

    def __str__(self) -> str:
        names = {
            0: "Ativo",
            1: "Transferido",
            2: "Desistente",
        }
        return names.get(self.value, f"Situação {self.value}")


class TipoEvento(str, Enum):
    FERIADO_NACIONAL = "FERIADO NACIONAL"
    FERIADO_MUNICIPAL = "FERIADO MUNICIPAL"
    DIA_NAO_LETIVO = "DIA NÃO LETIVO"
    REPOSICAO = "REPOSIÇÃO DE DIA LETIVO"
    REUNIAO_APM = "REUNIÃO DA APM"
    ESTUDOS = "Semana de estudos intensivos"

    @property
    def emoji(self) -> str:
        emojis = {
            "FERIADO": "🎉",
            "NÃO LETIVO": "🚫",
            "REPOSIÇÃO": "🔄",
            "REUNIÃO": "🤝",
            "ESTUDOS": "📝",
        }
        for key, emoji in emojis.items():
            if key in self.value.upper():
                return emoji
        return "📅"


class PerfilAviso(IntEnum):
    PROFESSOR = 1
    GESTAO = 4

    def __str__(self) -> str:
        names = {1: "Professor", 4: "Gestão"}
        return names.get(self.value, f"Perfil {self.value}")


class StatusTarefa(str, Enum):
    PENDENTE = "pending"
    RASCUNHO = "draft"
    CONCLUIDA = "completed"
    EXPIRADA = "expired"


class TipoAtividade(IntEnum):
    PROVA = 1
    TRABALHO = 2
    EXERCICIO = 3
    PARTICIPACAO = 4
    OUTRO = 99