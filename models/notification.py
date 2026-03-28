"""Fiz por fazer pois queria remover as notificações da SED pois são insuportaveis ai eu fiz modelo
    recomendo usar-lo para limpar as notificações da sed e deixar apenas do mural da Escola
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from functools import cached_property
from typing import TYPE_CHECKING

from .mixins import APIAccessibleMixin, SerializableMixin
from ..core.enums import Categoria, Prioridade, TipoAcao
from ..utils import HTML, format_relative_time

if TYPE_CHECKING:
    from ..core.state import ConnectionState

__all__ = ("Notificacao", "Link")

_DEADLINE_PATTERNS = [
    (
        re.compile(r"até\s+(\d{1,2})\s+de\s+(\w+)", re.IGNORECASE),
        "text_month",
    ),
    (
        re.compile(
            r"até\s+(\d{1,2})/(\d{1,2})(?:/(\d{4}))?", re.IGNORECASE
        ),
        "numeric_full",
    ),
    (
        re.compile(
            r"prazo[^:]*:\s*(?:até\s+)?(\d{1,2})/(\d{1,2})", re.IGNORECASE
        ),
        "numeric_short",
    ),
]

_MONTH_MAP = {
    "janeiro": 1,
    "fevereiro": 2,
    "março": 3,
    "marco": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}

_CATEGORIA_REGRAS: dict[Categoria, list[str]] = {
    Categoria.ESTAGIO: ["beem", "estágio", "estagio", "bolsa estágio"],
    Categoria.OLIMPIADA: ["olimp", "obmep", "omasp"],
    Categoria.MONITOR: ["monitor"],
    Categoria.WEBSERIE: ["websérie", "webserie", "episódio", "episodio"],
    Categoria.COPA: ["copa da escola"],
    Categoria.CURSO: ["curso técnico", "itinerário técnico", "vaga"],
}

_PRIORITY_URGENT = ["último dia", "última hora", "🚨", "urgente"]
_PRIORITY_HIGH = ["últimos dias", "faltam", "última semana"]

_ACAO_INSCRICAO = ["inscreva", "inscrição", "inscrições", "inscrever"]
_ACAO_ASSISTIR = ["assista", "confira", "youtu"]


@dataclass
class Link:
    """Link dentro da notificação."""
    url: str
    texto: str

    def __str__(self) -> str:
        return f"{self.texto} ({self.url})"


class Notificacao(APIAccessibleMixin, SerializableMixin):
    """Representa uma notificação da SEDUC.

    Attributes:
        id: ID da notificação
        id_global: ID global da notificação
        titulo: Título
        subtitulo: Subtítulo
        lida: Status de leitura
        criada_em: Data de criação
        categoria: Categoria classificada
        prioridade: Nível de prioridade
        tipo_acao: Tipo de ação sugerida
    """

    __slots__ = (
        "id",
        "id_global",
        "id_usuario",
        "titulo",
        "subtitulo",
        "lida",
        "imagem",
        "criada_em",
        "_html",
        "texto_limpo",
        "links",
        "prazo_final",
        "categoria",
        "tipo_acao",
        "prioridade",
        "_state",
    )

    def __init__(self, *, data: dict, state: ConnectionState) -> None:
        self._state = state

        self.id = data["idNotificacaoUsuario"]
        self.id_global = data["idNotificacao"]
        self.id_usuario = data["idUsuario"]

        self.titulo = data.get("titulo", "")
        self.subtitulo = data.get("subtitulo", "")
        self.lida = data.get("statusLeitura", False)
        self.imagem = data.get("urlImagem")

        self.criada_em = datetime.fromisoformat(data["dtInclusao"])

        self._html = data.get("mensagemCustomizavel", "")
        self.texto_limpo = self._extract_text()
        self.links = self._extract_links()

        self.prazo_final = self._extract_prazo()
        self.categoria = self._classificar_categoria()
        self.tipo_acao = self._classificar_acao()
        self.prioridade = self._classificar_prioridade()

    def __repr__(self) -> str:
        status = "✅" if self.lida else "📩"
        return f"<Notificacao {status} {self.titulo!r}>"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Notificacao):
            return self.id == other.id
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.id)

    @property
    def msg_id(self) -> int:
        """ID da mensagem (compatibilidade)."""
        return self.id

    @property
    def msg_titulo(self) -> str:
        """Título da mensagem (compatibilidade)."""
        return self.titulo

    @property
    def msg_texto(self) -> str:
        """Texto da mensagem (compatibilidade)."""
        return self.texto_limpo

    @property
    def msg_data(self) -> datetime:
        """Data da mensagem (compatibilidade)."""
        return self.criada_em

    @property
    def msg_lida(self) -> bool:
        """Status de leitura da mensagem (compatibilidade)."""
        return self.lida

    @property
    def msg_origem(self) -> str:
        """Origem da mensagem (compatibilidade)."""
        return "seduc"

    @property
    def tempo_atras(self) -> str:
        """Tempo relativo."""
        return format_relative_time(self.criada_em)

    @property
    def vencida(self) -> bool:
        """Diz se o prazo já passou."""
        if self.prazo_final:
            return datetime.now() > self.prazo_final
        return False

    @property
    def dias_restantes(self) -> int | None:
        """Dias até o fim do prazo."""
        if self.prazo_final:
            delta = self.prazo_final - datetime.now()
            return max(0, delta.days)
        return None

    async def mark_as_read(self) -> bool:
        """Marca a notificação como lida.

        Retorna:
            True se deu certo
        """
        from ..core.config import get_config

        config = get_config()

        headers = {"Ocp-Apim-Subscription-Key": config.SUBSCRIPTION_KEY2}

        resp = await self._http.put(
            f"{config.endpoints.cmsp_api}api/sala-do-futuro-alunos/leitura-notificacao-cmsp",
            params={"idNotificacaoUsuario": self.id},
            headers=headers,
        )

        if resp:
            self.lida = True
        return bool(resp)

        ler = mark_as_read

    def _extract_text(self) -> str:
        """Pega texto limpo do HTML."""
        return HTML.clean(self._html) if self._html else self.titulo

    def _extract_links(self) -> list[Link]:
        """Pega links do HTML."""
        if not self._html:
            return []

        links = []
        pattern = re.compile(
            r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
            re.DOTALL | re.IGNORECASE,
        )

        for match in pattern.finditer(self._html):
            url = match.group(1)
            texto = HTML.clean(match.group(2)) or url
            links.append(Link(url=url, texto=texto))

        return links

    def _extract_prazo(self) -> datetime | None:
        """Extrai prazo do texto usando padrões."""
        texto = self.texto_limpo
        ano_base = self.criada_em.year

        match = _DEADLINE_PATTERNS[0][0].search(texto)
        if match:
            dia = int(match.group(1))
            mes_nome = match.group(2).lower()
            if mes_nome in _MONTH_MAP:
                try:
                    return datetime(
                        ano_base, _MONTH_MAP[mes_nome], dia, 23, 59
                    )
                except ValueError:
                    pass

        match = _DEADLINE_PATTERNS[1][0].search(texto)
        if match:
            try:
                dia = int(match.group(1))
                mes = int(match.group(2))
                ano = (
                    int(match.group(3)) if match.group(3) else ano_base
                )
                return datetime(ano, mes, dia, 23, 59)
            except ValueError:
                pass

        match = _DEADLINE_PATTERNS[2][0].search(texto)
        if match:
            try:
                dia = int(match.group(1))
                mes = int(match.group(2))
                return datetime(ano_base, mes, dia, 23, 59)
            except ValueError:
                pass

        return None

    def _classificar_categoria(self) -> Categoria:
        """Classifica a categoria da notificação."""
        tudo = (self.titulo + " " + self.texto_limpo).lower()

        for categoria, palavras in _CATEGORIA_REGRAS.items():
            if any(p in tudo for p in palavras):
                return categoria

        return Categoria.OUTRO

    def _classificar_prioridade(self) -> Prioridade:
        """Classifica o nível de prioridade."""
        titulo = self.titulo.lower()

        if any(p in titulo for p in _PRIORITY_URGENT):
            return Prioridade.URGENTE

        if any(p in titulo for p in _PRIORITY_HIGH):
            return Prioridade.ALTA

        dias = self.dias_restantes
        if dias is not None:
            if dias <= 0:
                return Prioridade.URGENTE
            if dias <= 3:
                return Prioridade.ALTA
            if dias <= 7:
                return Prioridade.MEDIA

        return Prioridade.BAIXA

    def _classificar_acao(self) -> TipoAcao:
        """Classifica a ação sugerida."""
        tudo = (self.titulo + " " + self.texto_limpo).lower()

        if any(p in tudo for p in _ACAO_INSCRICAO):
            return TipoAcao.INSCRICAO
        if any(p in tudo for p in _ACAO_ASSISTIR):
            return TipoAcao.ASSISTIR
        if self.links:
            return TipoAcao.ACESSAR

        return TipoAcao.INFORMATIVO