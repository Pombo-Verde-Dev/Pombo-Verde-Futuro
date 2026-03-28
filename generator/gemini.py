from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.essay import EssayDetail, GeneratedEssay

__all__ = ("Generator",)


class Generator:
    """Gerador de redação com IA
    Precisa da variável de ambiente GEMINI_API_KEY ou de chave passada no construtor
    """

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self._model = None

        if self._api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self._api_key)
                self._model = genai.GenerativeModel("gemini-pro")
            except ImportError:
                pass

    @property
    def is_available(self) -> bool:
        """Verifica se o gerador está disponível"""
        return self._model is not None

    async def generate(
        self,
        detail: EssayDetail,
        temperature: float = 0.7,
    ) -> GeneratedEssay:
        """Gera redação usando IA.

        Parâmetros:
            detail: especificações da redação
            temperature: nível de criatividade (0.0-1.0)

        Retorna:
            GeneratedEssay com o conteúdo criado pela IA

        Raises:
            RuntimeError: se o gerador não estiver disponível
        """
        if not self.is_available:
            raise RuntimeError(
                "Generator not available. Install google-generativeai and set GEMINI_API_KEY"
            )

        from ..models.essay import GeneratedEssay

        start_time = time.time()

        prompt = self._build_prompt(detail)

        response = await self._model.generate_content_async(
            prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": 2048,
            },
        )

        text = response.text
        word_count = len(text.split())

        lines = text.strip().split("\n")
        title = detail.title or "Redação"
        body = text

        if len(lines) > 1 and len(lines[0]) < 100:
            title = lines[0].strip().lstrip("#").strip()
            body = "\n".join(lines[1:]).strip()

        return GeneratedEssay(
            title=title,
            text=body,
            word_count=word_count,
            generation_time=time.time() - start_time,
        )

    def _build_prompt(self, detail: EssayDetail) -> str:
        """Construir o prompt para a geração da redação"""
        prompt_parts = [
            f"Gênero: {detail.genre.name}",
            f"Tema: {detail.statement}",
        ]

        if detail.support_text:
            prompt_parts.append(f"Texto de apoio: {detail.support_text}")

        prompt_parts.extend([
            f"\nEscreva uma redação entre {detail.genre.min_words} e {detail.genre.max_words} palavras.",
            "Use linguagem formal e estrutura dissertativa.",
            "Inclua: introdução, desenvolvimento e conclusão.",
        ])

        if detail.skills:
            prompt_parts.append("\nCompetências a demonstrar:")
            for skill in detail.skills:
                prompt_parts.append(f"- {skill.name}: {skill.description}")

        return "\n".join(prompt_parts)