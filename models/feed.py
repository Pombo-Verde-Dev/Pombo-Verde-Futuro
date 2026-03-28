"""Não estou com vontade de explicar, é bem inutil"""

from __future__ import annotations

from datetime import datetime
from functools import cached_property
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .notification import Notificacao
    from .mural import Aviso
    from ..core.protocols import MensagemProtocol

__all__ = ("Feed",)


class Feed:
    """Reúne notificações e avisos num único feed

    Exemplo:
        >>> feed = Feed()
        >>> feed.add_items(*notifications, *mural_posts)
        >>> for item in feed.unread:
        ...     print(item.titulo)
    """

    def __init__(self) -> None:
        self._items: list[MensagemProtocol] = []
        self._sorted: list[MensagemProtocol] | None = None

    def __repr__(self) -> str:
        return f"<Feed items={len(self._items)} unread={len(self.unread)}>"

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self):
        return iter(self.todos)

    def __getitem__(self, index: int) -> MensagemProtocol:
        return self.todos[index]

    def add_items(self, *items: MensagemProtocol) -> None:
        """Adiciona itens no feed"""
        self._items.extend(items)
        self._sorted = None

    def add(self, *items: MensagemProtocol) -> None:
        """Atalho pra add_items"""
        self.add_items(*items)

    def clear(self) -> None:
        """Limpa todos os itens"""
        self._items.clear()
        self._sorted = None

    @property
    def todos(self) -> list[MensagemProtocol]:
        """Todos os itens ordenados por data (mais novo primeiro)"""
        if self._sorted is None:
            self._sorted = sorted(
                self._items, key=lambda m: m.msg_data, reverse=True
            )
        return self._sorted

    @property
    def unread(self) -> list[MensagemProtocol]:
        """Itens não lidos"""
        return [m for m in self.todos if not m.msg_lida]

    @property
    def read(self) -> list[MensagemProtocol]:
        """Itens lidos."""
        return [m for m in self.todos if m.msg_lida]

    @cached_property
    def _type_index(self) -> dict[type, list[MensagemProtocol]]:
        """Indexa itens por tipo pra filtrar mais rápido"""
        from .mural import Aviso
        from .notification import Notificacao

        index: dict[type, list[MensagemProtocol]] = {
            Aviso: [],
            Notificacao: [],
        }
        for m in self._items:
            if isinstance(m, Aviso):
                index[Aviso].append(m)
            elif isinstance(m, Notificacao):
                index[Notificacao].append(m)
        return index

    @property
    def from_school(self) -> list[Aviso]:
        """Só avisos da escola"""
        from .mural import Aviso
        return self._type_index.get(Aviso, [])

    @property
    def from_seduc(self) -> list[Notificacao]:
        """Só notificações da SEDUC"""
        from .notification import Notificacao
        return self._type_index.get(Notificacao, [])

    @property
    def pinned(self) -> list[Aviso]:
        """Avisos fixados"""
        return [m for m in self.from_school if m.fixado]

    @property
    def urgent(self) -> list[MensagemProtocol]:
        """Itens de prioridade alta"""
        from ..core.enums import Prioridade
        return [
            m
            for m in self._items
            if hasattr(m, "prioridade")
            and m.prioridade == Prioridade.URGENTE
        ]

    def search(self, term: str) -> list[MensagemProtocol]:
        """Busca no título e no conteúdo

        Args:
            term: Termo de busca

        Returns:
            Itens que batem com o termo
        """
        term = term.lower()
        return [
            m
            for m in self.todos
            if term in m.msg_titulo.lower() or term in m.msg_texto.lower()
        ]

    def filter_by_date(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[MensagemProtocol]:
        """Filtra por intervalo de data

        Args:
            start: Data/hora inicial
            end: Data/hora final

        Returns:
            Itens dentro do intervalo
        """
        items = self.todos
        if start:
            items = [m for m in items if m.msg_data >= start]
        if end:
            items = [m for m in items if m.msg_data <= end]
        return items

    @property
    def summary(self) -> dict:
        """Resumo das estatísticas do feed"""
        return {
            "total": len(self._items),
            "unread": len(self.unread),
            "read": len(self.read),
            "school": len(self.from_school),
            "seduc": len(self.from_seduc),
            "pinned": len(self.pinned),
            "urgent": len(self.urgent),
        }

    def to_dict(self) -> dict:
        """Converte pra dicionário"""
        return {
            "summary": self.summary,
            "items": [
                {
                    "id": m.msg_id,
                    "titulo": m.msg_titulo,
                    "texto": m.msg_texto[:100] + "..."
                    if len(m.msg_texto) > 100
                    else m.msg_texto,
                    "data": m.msg_data.isoformat(),
                    "lida": m.msg_lida,
                    "origem": m.msg_origem,
                }
                for m in self.todos
            ],
        }