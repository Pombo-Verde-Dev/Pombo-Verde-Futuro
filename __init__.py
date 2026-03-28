__title__ = "salafuturo"
__author__ = "Pombo Verde <github.com/Pombo-Verde-Dev>"
__license__ = "MIT"
__version__ = "1.0.0"

# Core
from .client import Client
from .core.errors import (
    SalaFuturoError,
    AuthenticationError,
    APIError,
    RateLimitError,
    NotFoundError,
    ForbiddenError,
    ValidationError,
)

# Enums
from .core.enums import (
    UF,
    Categoria,
    Prioridade,
    TipoAcao,
    Area,
    Turno,
    SituacaoMatricula,
    TipoEvento,
    PerfilAviso,
)

# Models
from .models import (
    User,
    Room,
    Escola,
    Materia,
    Falta,
    ResumoFaltas,
    Aula,
    EventoEscolar,
    Avaliacao,
    DiaAgenda,
    ResumoAvaliacoes,
    Aviso,
    Anexo,
    Autor,
    Notificacao,
    Link,
    Feed,
    Task,
    Essay,
)

# Utils
from .utils import (
    format_relative_time,
    HTML,
    encode_query,
    format_grade,
)

__all__ = (
    # Meta
    "__title__",
    "__version__",
    # Core
    "Client",
    # Errors
    "SalaFuturoError",
    "AuthenticationError",
    "APIError",
    "RateLimitError",
    "NotFoundError",
    "ForbiddenError",
    "ValidationError",
    # Enums
    "UF",
    "Categoria",
    "Prioridade",
    "TipoAcao",
    "Area",
    "Turno",
    "SituacaoMatricula",
    "TipoEvento",
    "PerfilAviso",
    # Models
    "User",
    "Room",
    "Escola",
    "Materia",
    "Falta",
    "ResumoFaltas",
    "Aula",
    "EventoEscolar",
    "Avaliacao",
    "DiaAgenda",
    "ResumoAvaliacoes",
    "Aviso",
    "Anexo",
    "Autor",
    "Notificacao",
    "Link",
    "Feed",
    "Task",
    "Essay",
    # Utils
    "format_relative_time",
    "HTML",
    "encode_query",
    "format_grade",
)