from __future__ import annotations

from datetime import datetime, date, time, timedelta
from typing import overload

__all__ = (
    "TimeUtil",
    "format_relative_time",
    "parse_iso_datetime",
    "calculate_duration",
)


class TimeUtil:
    """Classe utilitária para operações de tempo."""

    @staticmethod
    def now() -> datetime:
        """Retorna o datetime atual."""
        return datetime.now()

    @staticmethod
    def today() -> date:
        """Retorna a data atual."""
        return date.today()

    @staticmethod
    def parse_iso(value: str) -> datetime:
        """Parseia datetime em formato ISO."""
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    @staticmethod
    def format_relative(dt: datetime) -> str:
        """Formata datetime como tempo relativo."""
        delta = datetime.now() - dt

        if delta.days == 0:
            hours = delta.seconds // 3600
            if hours == 0:
                mins = delta.seconds // 60
                return f"{mins}min atrás" if mins > 0 else "agora"
            return f"{hours}h atrás"

        if delta.days == 1:
            return "ontem"

        if delta.days < 7:
            return f"{delta.days}d atrás"

        if delta.days < 30:
            weeks = delta.days // 7
            return f"{weeks}sem atrás"

        months = delta.days // 30
        return f"{months}m atrás"

    @staticmethod
    def days_between(start: datetime, end: datetime) -> int:
        """Calcula dias entre dois datetimes."""
        return max(0, (end - start).days)

    @staticmethod
    def is_within_range(
        dt: datetime, start: datetime, end: datetime
    ) -> bool:
        """Verifica se o datetime está dentro do intervalo."""
        return start <= dt <= end

    @staticmethod
    def progress_ratio(
        current: datetime, start: datetime, end: datetime
    ) -> float:
        """Calcula a proporção de progresso (0.0 a 1.0)."""
        total = (end - start).days
        if total <= 0:
            return 0.0
        passed = (current - start).days
        return min(1.0, max(0.0, passed / total))


def format_relative_time(dt: datetime) -> str:
    """Formata datetime como tempo relativo."""
    return TimeUtil.format_relative(dt)


def parse_iso_datetime(value: str) -> datetime:
    """Parseia string ISO de datetime."""
    return TimeUtil.parse_iso(value)


def calculate_duration(start: time, end: time) -> int:
    """Calcula duração em minutos entre dois horários."""
    dt_start = datetime.combine(date.today(), start)
    dt_end = datetime.combine(date.today(), end)
    return int((dt_end - dt_start).total_seconds() / 60)