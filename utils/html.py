from __future__ import annotations

import re
from html import unescape
from dataclasses import dataclass
from typing import Iterator

__all__ = (
    "HTML",
    "Link",
    "extract_text",
    "extract_links",
)


@dataclass
class Link:
    """Representa um hyperlink."""
    url: str
    text: str

    def __str__(self) -> str:
        return f"{self.text} ({self.url})"


class HTML:
    """Utilitários de parsing de HTML."""

    TAG_PATTERN = re.compile(r"<[^>]+>")
    BR_PATTERN = re.compile(r"<br\s*/?>", re.IGNORECASE)
    A_PATTERN = re.compile(
        r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
        re.DOTALL | re.IGNORECASE,
    )
    ENTITY_PATTERNS = {
        "&nbsp;": " ",
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        "&quot;": '"',
        "&#39;": "'",
    }

    @classmethod
    def clean(cls, html: str | None) -> str:
        """Remove tags HTML e decodifica entidades."""
        if not html:
            return ""

        text = cls.BR_PATTERN.sub("\n", html)
        text = cls.TAG_PATTERN.sub("", text)

        text = unescape(text)
        text = re.sub(r"\s+", " ", text).strip()

        return text

    @classmethod
    def extract_links(cls, html: str) -> list[Link]:
        """Extrai todos os links do HTML."""
        links = []
        for match in cls.A_PATTERN.finditer(html):
            url = match.group(1)
            text_raw = cls.TAG_PATTERN.sub("", match.group(2)).strip()
            text = text_raw or url
            links.append(Link(url=url, text=text))
        return links

    @classmethod
    def extract_text(cls, html: str | None) -> str:
        """Apelido para clean()."""
        return cls.clean(html)

    @classmethod
    def truncate(cls, html: str, length: int, suffix: str = "...") -> str:
        """Trunca texto HTML para o tamanho especificado."""
        text = cls.clean(html)
        if len(text) <= length:
            return text
        return text[:length].rsplit(" ", 1)[0] + suffix


# Convenience functions
def extract_text(html: str | None) -> str:
    """Extrai texto limpo do HTML."""
    return HTML.clean(html)


def extract_links(html: str) -> list[Link]:
    """Extrai links do HTML."""
    return HTML.extract_links(html)