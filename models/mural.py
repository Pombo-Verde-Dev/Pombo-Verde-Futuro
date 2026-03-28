"""Modelos relacionados ao mural de avisos.
    O principal modelo é o Aviso, que representa um aviso do mural, com título, conteúdo, autor, data de criação, etc
    Ele tem métodos para marcar como lido, verificar se é visível, se já expirou, etc
    Também tem os modelos Anexo (para arquivos anexados), Autor (quem postou) e Alteracao (registro de edições)
    Esses modelos são usados para organizar os dados dos avisos e facilitar o acesso às informações
    
    Dá pra fazer uma automação para quando tiver um aviso que preste o programa avisa
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from functools import cached_property
from typing import TYPE_CHECKING

from .mixins import APIAccessibleMixin, SerializableMixin, TimestampMixin
from ..core.enums import PerfilAviso
from ..utils import HTML, format_relative_time

if TYPE_CHECKING:
    from ..core.state import ConnectionState

__all__ = ("Aviso", "Anexo", "Autor", "Alteracao")

_DELTA_OPS_KEYS = frozenset(["insert", "attributes"])


@dataclass
class Anexo(SerializableMixin):
    """Anexo de arquivo."""
    nome: str
    url: str

    @property
    def extensao(self) -> str:
        """Extensão do arquivo."""
        return (
            self.nome.rsplit(".", 1)[-1].lower() if "." in self.nome else ""
        )

    @property
    def is_imagem(self) -> bool:
        """Diz se é imagem."""
        return self.extensao in ("png", "jpg", "jpeg", "gif", "webp", "bmp")

    @property
    def is_pdf(self) -> bool:
        """Diz se é PDF."""
        return self.extensao == "pdf"

    @property
    def is_video(self) -> bool:
        """Diz se é vídeo."""
        return self.extensao in ("mp4", "avi", "mkv", "mov")

    def __repr__(self) -> str:
        return f"<Anexo {self.nome!r}>"


@dataclass
class Autor(SerializableMixin):
    """Autor do aviso."""
    id: int
    nome: str

    @property
    def primeiro_nome(self) -> str:
        """Primeiro nome."""
        return self.nome.split()[0] if self.nome else ""

    def __repr__(self) -> str:
        return f"<Autor {self.nome!r}>"


@dataclass
class Alteracao(SerializableMixin):
    """Registro de alteração."""
    usuario_id: int
    usuario_nome: str
    data: datetime
    campo: str
    valor_anterior: str
    valor_novo: str

    def __repr__(self) -> str:
        return f"<Alteracao {self.campo} por {self.usuario_nome}>"


class Aviso(APIAccessibleMixin, SerializableMixin):
    """Representa um aviso do mural.

    Attributes:
        id: ID do aviso
        titulo: Título
        conteudo: Texto do aviso
        autor: Quem postou
        criado_em: Data de criação
        inicio: Quando fica visível
        fim: Quando acaba
        turmas: IDs das turmas alvo
        fixado: Se tá fixado
        lido: Se já foi lido
    """

    __slots__ = (
        "id",
        "perfil",
        "ativo",
        "titulo",
        "conteudo",
        "link",
        "_delta_raw",
        "delta",
        "autor",
        "criado_em",
        "inicio",
        "fim",
        "turmas",
        "fixado",
        "lido",
        "anexo",
        "alteracoes",
        "_state",
    )

    def __init__(self, *, data: dict, state: ConnectionState) -> None:
        self._state = state

        self.id = data["codigoMuralAviso"]
        self.perfil = PerfilAviso(data.get("perfilAviso", 1))
        self.ativo = data.get("ativo", True)

        self.titulo = data.get("titulo", "").strip()
        self.conteudo = data.get("conteudo", "").strip()
        self.link = data.get("link", "").strip()

        self._delta_raw = data.get("conteudoCustomizado", "[]")
        self.delta = self._parse_delta()

        self.autor = Autor(
            id=data.get("usuarioCadastro", 0),
            nome=data.get("nomeUsuarioCadastro", ""),
        )

        self.criado_em = datetime.fromisoformat(data["dataCadastro"])
        self.inicio = datetime.fromisoformat(data["dataInicio"])
        self.fim = datetime.fromisoformat(data["dataFim"])

        self.turmas = data.get("listaCodigoTurma", [])
        self.fixado = data.get("fixarAviso", False)
        self.lido = data.get("lido", False)

        self.anexo = self._parse_anexo(data)
        self.alteracoes = self._parse_alteracoes(data.get("alteracoes", []))

    def __repr__(self) -> str:
        pin = "📌" if self.fixado else "  "
        lido = "✅" if self.lido else "📩"
        return f"<Aviso {pin}{lido} {self.titulo!r} por {self.autor.nome}>"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Aviso):
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
        return self.conteudo

    @property
    def msg_data(self) -> datetime:
        """Data da mensagem (compatibilidade)."""
        return self.criado_em

    @property
    def msg_lida(self) -> bool:
        """Se a mensagem foi lida (compatibilidade)."""
        return self.lido

    @property
    def msg_origem(self) -> str:
        """Origem da mensagem (compatibilidade)."""
        return "escola"

    @property
    def tempo_atras(self) -> str:
        """Tempo relativo."""
        return format_relative_time(self.criado_em)

    @property
    def visivel(self) -> bool:
        """Diz se tá visível agora."""
        agora = datetime.now()
        return self.ativo and self.inicio <= agora <= self.fim

    @property
    def expirado(self) -> bool:
        """Diz se já expirou."""
        return datetime.now() > self.fim

    @property
    def agendado(self) -> bool:
        """Diz se ainda vai começar."""
        return datetime.now() < self.inicio

    @property
    def dias_restantes(self) -> int:
        """Dias até expirar."""
        delta = self.fim - datetime.now()
        return max(0, delta.days)

    @property
    def duracao_dias(self) -> int:
        """Duração total em dias."""
        delta = self.fim - self.inicio
        return max(0, delta.days)

    @property
    def perfil_nome(self) -> str:
        """Nome do perfil."""
        return str(self.perfil)

    @property
    def is_professor(self) -> bool:
        """Diz se veio de professor."""
        return self.perfil == PerfilAviso.PROFESSOR

    @property
    def is_gestao(self) -> bool:
        """Diz se veio da gestão."""
        return self.perfil == PerfilAviso.GESTAO

    @property
    def tem_anexo(self) -> bool:
        """Diz se tem anexo."""
        return self.anexo is not None

    @property
    def tem_link(self) -> bool:
        """Diz se tem link."""
        return bool(self.link)

    @property
    def editado(self) -> bool:
        """Diz se foi editado."""
        return len(self.alteracoes) > 0

    @property
    def abrangencia(self) -> int:
        """Quantidade de turmas alvo."""
        return len(self.turmas)

    @property
    def is_geral(self) -> bool:
        """Diz se é um aviso geral (muitas turmas)."""
        return self.abrangencia > 10

    @property
    def texto_formatado(self) -> str:
        """Texto formatado com markdown."""
        return self._render_delta()

    async def mark_as_read(self, user_id: int) -> bool:
        """Marca aviso como lido.

        Parâmetros:
            user_id: ID do usuário

        Retorna:
            True se deu certo
        """
        from ..core.config import get_config

        config = get_config()

        headers = {"Ocp-Apim-Subscription-Key": config.SUBSCRIPTION_KEY3}
        payload = {
            "usuarioVisualizacao": str(user_id),
            "codigoMuralAviso": self.id,
        }

        resp = await self._http.post(
            f"{config.endpoints.mural_api}api/mural-avisos/registrar-visualizacao-avisos",
            json=payload,
            headers=headers,
        )

        if resp:
            self.lido = True
        return bool(resp)

    ler = mark_as_read

    def pertence_a_turma(self, turma_id: int) -> bool:
        """Diz se mira em turma específica."""
        return turma_id in self.turmas

    def contem(self, termo: str) -> bool:
        """Procura no título e no conteúdo."""
        termo = termo.lower()
        return (
            termo in self.titulo.lower() or termo in self.conteudo.lower()
        )

    def _parse_delta(self) -> list[dict]:
        """Transforma Delta do Quill em lista."""
        if not self._delta_raw or self._delta_raw == "[]":
            return []
        try:
            parsed = json.loads(self._delta_raw)
            return parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, TypeError):
            return []

    @cached_property
    def _rendered_delta(self) -> str:
        """Renderiza Delta pra markdown (cacheado)."""
        if not self.delta:
            return self.conteudo

        partes: list[str] = []
        for op in self.delta:
            texto = op.get("insert", "")
            attrs = op.get("attributes", {})

            if not texto:
                continue

            if attrs.get("bold"):
                texto = f"**{texto.strip()}**"
            if attrs.get("italic"):
                texto = f"_{texto.strip()}_"
            if attrs.get("underline"):
                texto = f"__{texto.strip()}__"
            if attrs.get("strike"):
                texto = f"~~{texto.strip()}~~"

            partes.append(texto)

        return "".join(partes).strip()

    def _render_delta(self) -> str:
        """Renderiza Delta pra markdown."""
        return self._rendered_delta

    @staticmethod
    def _parse_anexo(data: dict) -> Anexo | None:
        """Transforma dados de anexo."""
        url = data.get("arquivo", "").strip()
        nome = data.get("nomeArquivo", "").strip()
        if url and nome:
            return Anexo(nome=nome, url=url)
        return None

    @staticmethod
    def _parse_alteracoes(raw: list) -> list[Alteracao]:
        """Parse edit history."""
        alteracoes = []
        for item in raw:
            try:
                alteracoes.append(
                    Alteracao(
                        usuario_id=item.get("usuarioAlteracao", 0),
                        usuario_nome=item.get("nomeUsuarioAlteracao", ""),
                        data=datetime.fromisoformat(item["dataAlteracao"]),
                        campo=item.get("campo", ""),
                        valor_anterior=item.get("valorAnterior", ""),
                        valor_novo=item.get("valorNovo", ""),
                    )
                )
            except (KeyError, ValueError):
                continue
        return alteracoes