"""Constantes relacionadas às disciplinas do ensino médio e técnico.
Não tem muito oq falar, é só um dicionário e enums de códigos pra nomes e emojis"""
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class Area(Enum):
    LINGUAGENS = auto()
    HUMANAS = auto()
    NATUREZA = auto()
    MATEMATICA = auto()
    TECNICO = auto()
    OUTROS = auto()


@dataclass(frozen=True)
class Disciplina:
    codigo: int
    nome: str
    emoji: str
    area: Area


DISCIPLINAS: dict[int, Disciplina] = {
    1100:  Disciplina(1100, "Língua Portuguesa", "📖", Area.LINGUAGENS),
    1900:  Disciplina(1900, "Educação Física", "⚽", Area.LINGUAGENS),
    8467:  Disciplina(8467, "Língua Inglesa", "🇬🇧", Area.LINGUAGENS),

    2100:  Disciplina(2100, "Geografia", "🌎", Area.HUMANAS),
    2200:  Disciplina(2200, "História", "📜", Area.HUMANAS),
    2300:  Disciplina(2300, "Sociologia", "🏛️", Area.HUMANAS),

    2400:  Disciplina(2400, "Biologia", "🧬", Area.NATUREZA),
    2600:  Disciplina(2600, "Física", "⚛️", Area.NATUREZA),
    2800:  Disciplina(2800, "Química", "🧪", Area.NATUREZA),

    2700:  Disciplina(2700, "Matemática", "🔢", Area.MATEMATICA),

    9929:  Disciplina(9929, "Carreira e Competências", "📚", Area.OUTROS),
    51000: Disciplina(51000, "Lógica e Programação", "👨‍💻", Area.TECNICO),
    51002: Disciplina(51002, "Redes e Segurança", "🌐", Area.TECNICO),
    51003: Disciplina(51003, "Processos de Desenvolvimento de Sistema", "📋", Area.TECNICO),

    # Especial
    -1:    Disciplina(-1, "Intervalo", "☕", Area.OUTROS),
}

EMOJIS_AREA: dict[Area, str] = {
    Area.LINGUAGENS: "📝",
    Area.HUMANAS:    "🌍",
    Area.NATUREZA:   "🔬",
    Area.MATEMATICA: "📐",
    Area.TECNICO:    "💻",
    Area.OUTROS:     "📚",
}

DIAS_SEMANA: dict[int, str] = {
    1: "Domingo",
    2: "Segunda-feira",
    3: "Terça-feira",
    4: "Quarta-feira",
    5: "Quinta-feira",
    6: "Sexta-feira",
    7: "Sábado",
}


def get_disciplina(codigo: int) -> Optional[Disciplina]:
    return DISCIPLINAS.get(codigo)


def get_por_area(area: Area) -> list[Disciplina]:
    return [d for d in DISCIPLINAS.values() if d.area == area]


def formatar_disciplina(codigo: int) -> str:
    disc = get_disciplina(codigo)
    if disc:
        return f"{disc.emoji} {disc.nome}"
    return f"Disciplina {codigo}"