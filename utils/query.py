from __future__ import annotations

from urllib.parse import urlencode
from typing import Any

__all__ = ("encode_query", "build_url")


def encode_query(params: dict[str, Any]) -> str:
    """Codifica dicionário em string de query para URL.

    Trata listas e valores aninhados.
    """
    flattened = []

    for key, value in params.items():
        if value is None:
            continue
        elif isinstance(value, list):
            for item in value:
                flattened.append((key, str(item)))
        elif isinstance(value, bool):
            flattened.append((key, str(value).lower()))
        else:
            flattened.append((key, str(value)))

    return urlencode(flattened)


def build_url(base: str, params: dict[str, Any] | None = None) -> str:
    """Cria URL com parâmetros de query."""
    if not params:
        return base

    query = encode_query(params)
    separator = "&" if "?" in base else "?"
    return f"{base}{separator}{query}"