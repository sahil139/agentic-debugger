from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel


class BaseAgent(ABC):
    """Abstract agent with a shared interface and LLM helper."""

    def __init__(self, llm: BaseChatModel, name: str) -> None:
        self.llm = llm
        self.name = name

    @abstractmethod
    def run(self, input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent. Must return a JSON-serializable dict."""
        raise NotImplementedError

    def _ask_llm(self, system_prompt: str, user_prompt: str) -> str:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        response = self.llm.invoke(messages)
        # Some providers return a Message, others a string; normalize to string
        content = getattr(response, "content", None)
        return content if isinstance(content, str) else str(response)



