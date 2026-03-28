from __future__ import annotations

from typing import Any

__all__ = (
    "TableFormatter",
    "format_grade",
    "format_percentage",
)


class TableFormatter:
    """Formata dados como tabelas."""

    @staticmethod
    def format_dict(data: dict[str, Any], title: str | None = None) -> str:
        """Formata o dicionário em pares chave-valor alinhados."""
        if not data:
            return "No data"

        max_key = max(len(str(k)) for k in data.keys())
        lines = []

        if title:
            lines.append(f"\n{'=' * (max_key + 20)}")
            lines.append(f"  {title}")
            lines.append(f"{'=' * (max_key + 20)}\n")

        for key, value in data.items():
            lines.append(f"  {str(key):<{max_key}} │ {value}")

        return "\n".join(lines)

    @staticmethod
    def format_list(
        items: list[Any], headers: list[str] | None = None
    ) -> str:
        """Formata lista como tabela."""
        if not items:
            return "No items"

        if headers:
            return f"  {' │ '.join(headers)}\n" + "\n".join(
                f"  {item}" for item in items
            )

        return "\n".join(f"  • {item}" for item in items)


def format_grade(value: float | None) -> str:
    """Format grade with proper precision."""
    if value is None:
        return "—"
    if value == int(value):
        return str(int(value))
    return f"{value:.1f}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format as percentage."""
    return f"{value:.{decimals}f}%"