from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final
import os

__all__ = ("Config", "APIEndpoints")


@dataclass(frozen=True)
class APIEndpoints:
    """API dominios urls"""
    SED_BASE: str = "https://sedintegracoes.educacao.sp.gov.br/"
    EDUSP_BASE: str = "https://edusp-api.ip.tv"

    @property
    def sed_api(self) -> str:
        return f"{self.SED_BASE}saladofuturobffapi/"

    @property
    def mural_api(self) -> str:
        return f"{self.SED_BASE}muralavisosapi/"

    @property
    def cmsp_api(self) -> str:
        return f"{self.SED_BASE}cmspwebservice/"


@dataclass
class Config:
    SUBSCRIPTION_KEY: str = field(
        default_factory=lambda: os.getenv(
            "SED_SUBSCRIPTION_KEY", "" # vc que vai atrás da chave, não vou deixar aqui kkkk
        )
    )
    SUBSCRIPTION_KEY2: str = field(
        default_factory=lambda: os.getenv(
            "SED_SUBSCRIPTION_KEY2", "" # aqui tbm não vou deixar a chave
        )
    )
    SUBSCRIPTION_KEY3: str = field(
        default_factory=lambda: os.getenv(
            "SED_SUBSCRIPTION_KEY3", "" # Não quero a sed me caçando dps
        )
    )

    endpoints: APIEndpoints = field(default_factory=APIEndpoints)

    DEFAULT_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    BACKOFF_FACTOR: float = 2.0

    CACHE_ENABLED: bool = True
    CACHE_TTL: int = 300
    CACHE_MAX_SIZE: int = 1000

    EXTRA_TARGETS: tuple[str, ...] = ("1052", "1820", "764")

    DEFAULT_DURATION: float = 2431.63

    HEADERS: dict[str, str] = field(default_factory=lambda: {
        "User-Agent": "", # use o seu user agent,
        "Accept": "application/json",
        "Origin": "https://saladofuturo.educacao.sp.gov.br",
        "Referer": "https://saladofuturo.educacao.sp.gov.br/",
        "x-api-platform": "webclient",
        "x-api-realm": "edusp",
    })

    def get_subscription_key(self, level: int = 1) -> str:
        keys = {
            1: self.SUBSCRIPTION_KEY,
            2: self.SUBSCRIPTION_KEY2,
            3: self.SUBSCRIPTION_KEY3,
        }
        return keys.get(level, self.SUBSCRIPTION_KEY)


_global_config: Config | None = None


def get_config() -> Config:
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config


def set_config(config: Config) -> None:
    global _global_config
    _global_config = config