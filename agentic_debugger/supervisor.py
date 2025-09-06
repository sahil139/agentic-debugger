from __future__ import annotations

from typing import Any, Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from langchain_core.language_models.chat_models import BaseChatModel

from .agents import (
    LogAgent,
    MetricsAgent,
    DesignReviewAgent,
    RootCauseAgent,
    PostmortemAgent,
)


class SupervisorAgent:
    """Coordinates the specialized agents and merges their outputs."""

    def __init__(self, llm: BaseChatModel) -> None:
        self.llm = llm
        self.log_agent = LogAgent(llm)
        self.metrics_agent = MetricsAgent(llm)
        self.design_agent = DesignReviewAgent(llm)
        self.rootcause_agent = RootCauseAgent(llm)
        self.postmortem_agent = PostmortemAgent(llm)

    def run(self, input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []

        # 1) First-tier agents (parallel): Log + Metrics
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(self._safe_run, self.log_agent, input, context): "log",
                executor.submit(self._safe_run, self.metrics_agent, input, context): "metrics",
            }
            log_result: Dict[str, Any] = {}
            metrics_result: Dict[str, Any] = {}
            for fut in as_completed(futures):
                tag = futures[fut]
                result = fut.result()
                if tag == "log":
                    log_result = result
                else:
                    metrics_result = result

        # 2) DesignReviewAgent (can leverage prior outputs if needed)
        design_context = dict(context or {})
        design_context.update({
            "log_result": log_result.get("details", {}),
            "metrics_result": metrics_result.get("details", {}),
        })
        design_result = self._safe_run(self.design_agent, input, design_context)
        results.extend([log_result, metrics_result, design_result])

        # 2) Root cause uses above outputs
        rc_context = dict(context or {})
        rc_context.update({
            "log_result": log_result.get("details", {}),
            "metrics_result": metrics_result.get("details", {}),
            "design_result": design_result.get("details", {}),
        })
        rootcause_result = self._safe_run(self.rootcause_agent, input, rc_context)
        results.append(rootcause_result)

        # 4) Postmortem last (include root cause and optional timeline)
        pm_context = dict(context or {})
        pm_context["root_cause_result"] = rootcause_result.get("details", {})
        postmortem_result = self._safe_run(self.postmortem_agent, input, pm_context)
        results.append(postmortem_result)

        merged_summary = "\n\n".join([r.get("summary", "").strip() for r in results if r.get("summary")])
        consolidated_json = {
            "orchestrator": "SupervisorAgent",
            "input": input,
            "context": context,
            "agents": results,
            "combined_summary": merged_summary,
        }

        consolidated_markdown = self._compose_markdown(results, merged_summary)
        consolidated_json["markdown_report"] = consolidated_markdown
        return consolidated_json

    def _safe_run(self, agent, input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return agent.run(input=input, context=context)
        except Exception as exc:
            return {
                "agent": getattr(agent, "name", agent.__class__.__name__),
                "summary": f"Agent failed: {exc}",
                "details": {"error": str(exc)},
            }

    def _compose_markdown(self, results: List[Dict[str, Any]], merged_summary: str) -> str:
        lines: List[str] = []
        lines.append("# Incident Analysis Report")
        lines.append("")
        lines.append("## Summary")
        lines.append(merged_summary or "No summary available.")
        lines.append("")

        # If PostmortemAgent produced a markdown, prefer that as the main body
        postmortem = next((r for r in results if r.get("agent") == "PostmortemAgent"), None)
        pm_md = None
        if postmortem:
            pm_md = (postmortem.get("details", {}) or {}).get("markdown_report")
        if pm_md:
            lines.append(pm_md)
        else:
            # Build a minimal appendix
            for r in results:
                agent_name = r.get("agent", "Agent")
                lines.append("")
                lines.append(f"## {agent_name}")
                lines.append(r.get("summary", ""))

        return "\n".join(lines)


