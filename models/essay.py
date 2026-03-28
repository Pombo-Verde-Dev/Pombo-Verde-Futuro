"""Unico modelo que eu fiz um post na questão de tarefas
    A IA responde a redação com base ao conteudo solicitado pela sed
    Aqui tbm tem varioas dados da redação só vc ir ler as docstrings para entender melhor
    """

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

from .mixins import APIAccessibleMixin, SerializableMixin
from ..core.errors import APIError
from ..utils import HTML

if TYPE_CHECKING:
    from ..core.state import ConnectionState

__all__ = (
    "Essay",
    "EssayDetail",
    "EssayConfig",
    "Genre",
    "Skill",
    "GeneratedEssay",
    "AnswerDraft",
)


@dataclass
class Skill(SerializableMixin):
    """Avaliação da redação (gerado pela sala do futuro)"""
    name: str
    description: str
    weight: float


@dataclass
class Genre(SerializableMixin):
    """Especificações da Redação"""
    name: str
    min_words: int
    max_words: int
    language: str = "pt-BR"


@dataclass
class EssayConfig(SerializableMixin):
    """Configaração da Redação"""
    allow_copy_paste: bool
    manuscript_only: bool
    allow_transcript: bool
    essay_images: str


@dataclass
class EssayDetail(SerializableMixin):
    """Informações detalhada da redação"""
    task_id: str
    question_id: str
    title: str
    description: str
    expire_at: str | None
    genre: Genre
    statement: str
    support_text: str
    skills: list[Skill]
    config: EssayConfig


@dataclass
class GeneratedEssay(SerializableMixin):
    """Gere-AI redação"""
    title: str
    text: str
    word_count: int
    generation_time: float


@dataclass
class AnswerDraft(SerializableMixin):
    """Rascunho para entrga da redação."""
    id: int
    task_id: str
    status: str
    created_at: str
    updated_at: str
    raw: dict[str, Any] = field(repr=False)


class Essay(APIAccessibleMixin, SerializableMixin):
    """Representa a lição da redação
    
    Attributes:
        id: Redação ID
        title: Redação titulo
        author: Autor nome
        expire_at: Data da expiração
        question_count: Numero de questões
        answer_id: ID da resposta atual
    """
    
    __slots__ = (
        "id", "title", "author", "expire_at",
        "question_count", "answer_id", "detail",
        "_room", "_state"
    )
    
    def __init__(
        self,
        *,
        data: dict,
        room_name: str,
        state: ConnectionState,
    ) -> None:
        self._state = state
        self._room = room_name
        
        self.id = str(data.get("id"))
        self.title = data.get("title", "")
        self.author = data.get("author")
        self.expire_at = data.get("expire_at")
        self.question_count = data.get("question_count", 0)
        self.answer_id = data.get("answer_id")
        self.detail: EssayDetail | None = None
    
    def __repr__(self) -> str:
        return f"<Essay id={self.id!r} title={self.title!r}>"
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Essay):
            return self.id == other.id
        return NotImplemented
    
    def __hash__(self) -> int:
        return hash(self.id)
    
    async def fetch_detail(self) -> EssayDetail:
        """Busque por detalhes da redações
        
        Returns:
            EssayDetail com todas especificações
            
        Raises:
            APIError: Se a redação não tiver dados
        """
        from ..core.config import get_config
        config = get_config()
        
        resp = await self._http.get(
            f"{config.endpoints.EDUSP_BASE}/tms/task/{self.id}/apply",
            params={
                "preview_mode": "false",
                "token_code": "null",
                "room_name": self._room,
            },
        )
        
        if not resp or not resp.get("questions"):
            raise APIError(f"Essay {self.id} has no data")
        
        self.detail = self._parse_detail(resp, resp["questions"][0])
        return self.detail
    
    async def generate(self, temperature: float = 0.7) -> GeneratedEssay:
        """Gere redações usando IA.
        
        Args:
            temperature: Creatividade da IA (0.0-1.0)
            
        Returns:
            GeneratedEssay Com conteudo da IA
        """
        if not self.detail:
            await self.fetch_detail()
        
        return await self._state.generator.generate(self.detail, temperature)
    
    async def submit(
        self,
        title: str,
        body: str,
        duration: float = 0.0,
    ) -> AnswerDraft:
        """Envie a resposta da redação

        Args:
            title: Redaição titulo
            body: Corpo da redação
            duration: Tempo de gasto escrevendo

        Returns:
            AnswerDraft ccom status de envio
        """
        from ..core.config import get_config
        config = get_config()

        if not self.detail:
            await self.fetch_detail()

        payload = self._build_payload(self.detail.question_id, title, body, duration)

        try:
            resp = await self._http.post(
                f"{config.endpoints.EDUSP_BASE}/tms/task/{self.id}/answer",
                json=payload,
            )
        except APIError as exc:
            if "task already answered" in str(exc).lower():
                return await self._update(payload)
            raise

        if not resp:
            raise APIError(f"No response saving draft {self.id}")

        return self._to_draft(resp)
    
    async def _update(self, payload: dict) -> AnswerDraft:
        """Atualiza a redação já salva"""
        if not self.answer_id:
            raise APIError("Task already answered but answer_id unavailable")
        
        from ..core.config import get_config
        config = get_config()
        
        resp = await self._http.put(
            f"{config.endpoints.EDUSP_BASE}/tms/task/{self.id}/answer/{self.answer_id}",
            json=payload,
        ) or {}
        
        return AnswerDraft(
            id=self.answer_id,
            task_id=self.id,
            status=resp.get("status", "draft"),
            created_at=resp.get("created_at", ""),
            updated_at=resp.get("updated_at", ""),
            raw=resp,
        )
    
    def _build_payload(
        self,
        question_id: str,
        title: str,
        body: str,
        duration: float,
    ) -> dict:
        """Contruir status de envio"""
        from ..core.config import get_config
        config = get_config()

        return {
            "status": "draft",
            "answers": {
                question_id: {
                    "question_id": int(question_id),
                    "question_type": "essay",
                    "answer": {"title": title, "body": body},
                }
            },
            "accessed_on": "room",
            "executed_on": self._room,
            "duration": duration or getattr(config, 'DEFAULT_DURATION', 3600),
        }
    
    def _parse_detail(self, resp: dict, question: dict) -> EssayDetail:
        """Analisar a resposta da api para EssayDetail"""
        opts = question.get("options", {})
        genre_data = opts.get("genre", {})
        
        return EssayDetail(
            task_id=self.id,
            question_id=str(question.get("id", "")),
            title=resp.get("title", ""),
            description=HTML.clean(resp.get("description", "")),
            expire_at=resp.get("expire_at"),
            genre=Genre(
                name=genre_data.get("statement", "Redação"),
                min_words=genre_data.get("min_word", 0),
                max_words=genre_data.get("max_word", 0),
                language=genre_data.get("language", "pt-BR"),
            ),
            statement=HTML.clean(question.get("statement", "")),
            support_text=HTML.clean(opts.get("support_text", "")),
            skills=[
                Skill(
                    s.get("statement", ""),
                    HTML.clean(s.get("description", "")),
                    s.get("weight", 1),
                )
                for s in genre_data.get("assessed_skills", [])
            ],
            config=EssayConfig(
                allow_copy_paste=opts.get("allow_copy_paste", False),
                manuscript_only=opts.get("manuscript_essay_only", False),
                allow_transcript=opts.get("allow_essay_transcript", True),
                essay_images=opts.get("essay_images_uploader", "any"),
            ),
        )
    
    @staticmethod
    def _to_draft(resp: dict) -> AnswerDraft:
        """Converter resposta em AnswerDraft."""
        return AnswerDraft(
            id=resp["id"],
            task_id=str(resp["task_id"]),
            status=resp["status"],
            created_at=resp["created_at"],
            updated_at=resp["updated_at"],
            raw=resp,
        )