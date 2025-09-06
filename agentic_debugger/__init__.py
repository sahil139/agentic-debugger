"""
Agentic Debugger package.

Provides a suite of analysis agents (logs, metrics, design review, root cause,
postmortem) orchestrated by a supervisor, backed by a local LLM "gpt-oasis" via LangChain.
"""

from .llm import get_llm
from .agents import (
    BaseAgent,
    LogAgent,
    MetricsAgent,
    DesignReviewAgent,
    RootCauseAgent,
    PostmortemAgent,
)
from .supervisor import SupervisorAgent

__all__ = [
    "get_llm",
    "BaseAgent",
    "LogAgent",
    "MetricsAgent",
    "DesignReviewAgent",
    "RootCauseAgent",
    "PostmortemAgent",
    "SupervisorAgent",
]



