from __future__ import annotations

import logging
from typing import Protocol

from app.utils.config import get_settings

logger = logging.getLogger(__name__)


class LLM(Protocol):
    def generate(self, system_prompt: str, user_prompt: str, temperature: float, model: str) -> str:
        ...


class OpenAIChatLLM:
    def __init__(self, api_key: str | None):
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required for OpenAI LLM")
        self.api_key = api_key

    def generate(self, system_prompt: str, user_prompt: str, temperature: float, model: str) -> str:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = ChatOpenAI(model=model, temperature=temperature, api_key=self.api_key)
        response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
        return response.content


class LocalStubLLM:
    def generate(self, system_prompt: str, user_prompt: str, temperature: float, model: str) -> str:
        if "Source [1]" in user_prompt:
            return "Stub response based on the provided sources. See [1]."
        return "Stub response: no sources available."


def get_llm() -> LLM:
    settings = get_settings()
    if settings.use_local_llm:
        logger.info("Using local stub LLM")
        return LocalStubLLM()
    return OpenAIChatLLM(settings.openai_api_key)
