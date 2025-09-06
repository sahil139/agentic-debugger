from __future__ import annotations

import os
from typing import Optional

from langchain_openai import ChatOpenAI


def get_llm(
    model: str = "gpt-oasis",
    temperature: float = 0.2,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
):
    """
    Return a LangChain Chat LLM configured for a local "gpt-oasis" endpoint.

    Environment variables (overridable by arguments):
      - GPOASIS_BASE_URL: default "http://localhost:8080/v1"
      - GPOASIS_API_KEY: default "sk-no-key" (some servers require a non-empty value)
    """
    effective_base_url = base_url or os.getenv("GPOASIS_BASE_URL", "http://localhost:8080/v1")
    effective_api_key = api_key or os.getenv("GPOASIS_API_KEY", "sk-no-key")

    # ChatOpenAI from langchain-openai supports custom base_url for OpenAI-compatible servers
    llm = ChatOpenAI(
        model=model,
        temperature=temperature,
        base_url=effective_base_url,
        api_key=effective_api_key,
    )
    return llm



