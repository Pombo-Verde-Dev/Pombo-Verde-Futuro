""""Modelos que representa as tarefaas.
Bom, era para ter mais coisas, como que n foquei nessa parte de tarefas eu só coloquei isso.
Na api tem mais dados para vc uasr, só que fiquei com preguiça de pegar e colocar aqui
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .mixins import APIAccessibleMixin, SerializableMixin
from ..utils import HTML

if TYPE_CHECKING:
    from ..core.state import ConnectionState

__all__ = ("Task", "Question")


class Question(SerializableMixin):
    """Representa uma questão da tarefa."""

    __slots__ = ("id", "title", "type")

    def __init__(self, *, data: dict) -> None:
        self.id = str(data.get("id", ""))
        self.title = HTML.clean(data.get("statement", ""))
        self.type = data.get("type", "")

    def __repr__(self) -> str:
        return f"<Question id={self.id!r}>"


class Task(APIAccessibleMixin, SerializableMixin):
    """Representa uma tarefa escolar.

    Attributes:
        id: ID da tarefa
        title: Título da tarefa
    """

    __slots__ = ("id", "title", "_room", "_state")

    def __init__(
        self,
        *,
        data: dict,
        room_name: str,
        state: ConnectionState,
    ) -> None:
        self._state = state
        self._room = room_name

        self.id = str(data["id"])
        self.title = data.get("title", "")

    def __repr__(self) -> str:
        return f"<Task id={self.id!r} title={self.title!r}>"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Task):
            return self.id == other.id
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.id)

    async def fetch_questions(self) -> list[Question]:
        """Busca as questões da tarefa.

        Retorna:
            Lista de Question
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

        questions = (resp or {}).get("questions", [])
        return [Question(data=q) for q in questions]