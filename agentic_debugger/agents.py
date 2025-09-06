from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple
from statistics import mean, stdev

from .base import BaseAgent


def _format_context(context: Dict[str, Any]) -> str:
    parts: List[str] = []
    for key, value in (context or {}).items():
        parts.append(f"- {key}: {value}")
    return "\n".join(parts)


class LogAgent(BaseAgent):
    def __init__(self, llm) -> None:
        super().__init__(llm, name="LogAgent")

    def run(self, input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        text = _read_text_maybe_file(input)
        parsed = _parse_logs(text)
        summary = _summarize_logs(parsed)
        return {"agent": self.name, "summary": summary, "details": parsed}


class MetricsAgent(BaseAgent):
    def __init__(self, llm) -> None:
        super().__init__(llm, name="MetricsAgent")

    def run(self, input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        # Expect metrics in context as { metric_name: [{"ts": int|str, "value": float}, ...], ... }
        # If not present, try to parse JSON from input.
        metrics: Dict[str, List[Dict[str, Any]]] = {}
        raw_context_metrics = context.get("metrics") if isinstance(context, dict) else None
        if isinstance(raw_context_metrics, dict):
            metrics = raw_context_metrics  # type: ignore[assignment]
        else:
            parsed_json = _maybe_parse_json(input)
            if isinstance(parsed_json, dict) and any(isinstance(v, list) for v in parsed_json.values()):
                metrics = parsed_json  # type: ignore[assignment]

        analysis = _analyze_metrics(metrics)
        summary = _summarize_metrics(analysis)
        return {"agent": self.name, "summary": summary, "details": analysis}


class DesignReviewAgent(BaseAgent):
    def __init__(self, llm) -> None:
        super().__init__(llm, name="DesignReviewAgent")

    def run(self, input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        arch = _parse_architecture(input, context)
        analysis = _analyze_design(arch)

        # Ask LLM to provide an explanation based on structured findings
        system = (
            "You are a senior systems architect. Provide a concise explanation of the risks, "
            "redundancy improvements, and scalability concerns, grounded in the provided JSON."
        )
        user = (
            "Architecture findings (JSON):\n" + json.dumps(analysis, indent=2) + "\n\n"
            "Write a short explanation (<= 10 lines) with prioritized recommendations."
        )
        try:
            explanation = self._ask_llm(system, user).strip()
        except Exception:
            explanation = ""

        summary = _summarize_design(analysis)
        analysis["explanation"] = explanation
        return {"agent": self.name, "summary": summary, "details": analysis}


class RootCauseAgent(BaseAgent):
    def __init__(self, llm) -> None:
        super().__init__(llm, name="RootCauseAgent")

    def run(self, input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        # Expect prior agent results in context under keys: log_result, metrics_result, design_result
        log_result = context.get("log_result", {}) if isinstance(context, dict) else {}
        metrics_result = context.get("metrics_result", {}) if isinstance(context, dict) else {}
        design_result = context.get("design_result", {}) if isinstance(context, dict) else {}

        payload = {
            "incident_input": input,
            "logs": log_result,
            "metrics": metrics_result,
            "design": design_result,
        }

        system = (
            "You are a reliability engineer specializing in root cause analysis (RCA). "
            "Given structured findings from logs, metrics, and design review, infer a single most likely root cause. "
            "Return STRICT JSON with keys: root_cause (string), confidence_score (0..1 float), explanation (string)."
        )
        user = (
            "Findings JSON:\n" + json.dumps(payload, indent=2) + "\n\n"
            "Respond only with a JSON object and no additional text."
        )
        content = self._ask_llm(system, user).strip()
        parsed = _extract_json_object(content)
        if not isinstance(parsed, dict):
            parsed = {"root_cause": "unknown", "confidence_score": 0.3, "explanation": content}

        # Build a compact summary
        summary = f"Root cause: {parsed.get('root_cause', 'unknown')} (confidence {parsed.get('confidence_score', 0):.2f})"
        return {"agent": self.name, "summary": summary, "details": parsed}


class PostmortemAgent(BaseAgent):
    def __init__(self, llm) -> None:
        super().__init__(llm, name="PostmortemAgent")

    def run(self, input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        # Expected in context:
        # - root_cause_result: { root_cause, confidence_score, explanation }
        # - timeline: list of events {ts, type, description}
        root_cause = (context or {}).get("root_cause_result", {})
        timeline = (context or {}).get("timeline", [])

        json_report = _build_postmortem_json(
            incident_input=input,
            root_cause=root_cause,
            timeline=timeline,
            extras={"context": {k: v for k, v in (context or {}).items() if k not in {"root_cause_result"}}},
        )

        # Use LLM to render a polished Markdown postmortem
        system = "You write clear, concise technical postmortems."
        user = (
            "Draft a postmortem in Markdown with sections: What Happened, Impact, Root Cause, Mitigation, Action Items.\n"
            "Use this JSON as source of truth and keep it short and actionable.\n\n"
            + json.dumps(json_report, indent=2)
        )
        try:
            markdown = self._ask_llm(system, user).strip()
        except Exception:
            markdown = _fallback_markdown_from_json(json_report)

        summary = f"Postmortem prepared. Root cause: {root_cause.get('root_cause', 'unknown')}"
        return {"agent": self.name, "summary": summary, "details": {"json_report": json_report, "markdown_report": markdown}}


# -------------------------
# Helpers: Logs
# -------------------------

LOG_ERROR_PATTERNS = [
    re.compile(r"\b(ERROR|FATAL|CRITICAL)\b", re.IGNORECASE),
    re.compile(r"\bException:\s*(.+)$", re.IGNORECASE),
]

STACK_TRACE_START = re.compile(r'^(Traceback \(most recent call last\):|\tat\s.+|\s*File ")')


def _read_text_maybe_file(maybe_path: str) -> str:
    candidate = (maybe_path or "").strip()
    if not candidate:
        return ""
    try:
        if os.path.isfile(candidate):
            with open(candidate, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
    except Exception:
        pass
    return candidate


def _parse_logs(text: str) -> Dict[str, Any]:
    lines = text.splitlines()
    errors: List[Dict[str, Any]] = []
    anomalies: List[Dict[str, Any]] = []
    stack_traces: List[str] = []

    current_stack: List[str] = []
    in_stack = False

    for idx, line in enumerate(lines):
        # Detect error markers
        if any(p.search(line) for p in LOG_ERROR_PATTERNS):
            errors.append({"line": idx + 1, "message": line.strip()})

        # Naive anomaly: very long line or repeated 'timeout'/'refused'
        if len(line) > 500 or re.search(r"timeout|refused|unavailable", line, re.I):
            anomalies.append({"line": idx + 1, "message": line.strip()})

        # Stack trace accumulation
        if STACK_TRACE_START.search(line):
            if in_stack and current_stack:
                stack_traces.append("\n".join(current_stack))
                current_stack = []
            in_stack = True
            current_stack.append(line.rstrip())
        elif in_stack:
            if line.strip() == "":
                stack_traces.append("\n".join(current_stack))
                current_stack = []
                in_stack = False
            else:
                current_stack.append(line.rstrip())

    if in_stack and current_stack:
        stack_traces.append("\n".join(current_stack))

    return {
        "errors": errors,
        "anomalies": anomalies,
        "stack_traces": stack_traces,
        "counts": {
            "errors": len(errors),
            "anomalies": len(anomalies),
            "stack_traces": len(stack_traces),
        },
    }


def _summarize_logs(parsed: Dict[str, Any]) -> str:
    c = parsed.get("counts", {})
    return (
        f"Detected {c.get('errors', 0)} errors, {c.get('anomalies', 0)} anomalies, "
        f"and {c.get('stack_traces', 0)} stack traces."
    )


# -------------------------
# Helpers: Metrics
# -------------------------

def _maybe_parse_json(text: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(text)
    except Exception:
        return None


def _z_scores(values: List[float]) -> List[float]:
    if len(values) < 2:
        return [0.0 for _ in values]
    mu = mean(values)
    try:
        sigma = stdev(values)
    except Exception:
        sigma = 0.0
    if sigma == 0:
        return [0.0 for _ in values]
    return [(v - mu) / sigma for v in values]


def _rolling_stats(values: List[float], window: int = 5) -> Tuple[List[float], List[float]]:
    means: List[float] = []
    stds: List[float] = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        window_vals = values[start : i + 1]
        m = mean(window_vals)
        s = stdev(window_vals) if len(window_vals) >= 2 else 0.0
        means.append(m)
        stds.append(s)
    return means, stds


def _analyze_metrics(metrics: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    analysis: Dict[str, Any] = {"metrics": {}, "summary": {}}
    for name, series in metrics.items():
        values: List[float] = []
        timestamps: List[Any] = []
        for point in series:
            try:
                v = float(point.get("value"))
                values.append(v)
                timestamps.append(point.get("ts"))
            except Exception:
                continue

        if not values:
            continue

        z = _z_scores(values)
        roll_mean, roll_std = _rolling_stats(values, window=5)

        anomalies: List[Dict[str, Any]] = []
        for i, v in enumerate(values):
            z_i = z[i]
            m_i = roll_mean[i]
            s_i = roll_std[i]
            dev = (v - m_i) / (s_i if s_i != 0 else 1.0)
            if abs(z_i) >= 3.0 or abs(dev) >= 3.0:
                anomalies.append({
                    "index": i,
                    "ts": timestamps[i],
                    "value": v,
                    "z_score": z_i,
                    "rolling_mean": m_i,
                    "rolling_std": s_i,
                    "rolling_deviation": dev,
                })

        analysis["metrics"][name] = {
            "points": len(values),
            "anomalies": anomalies,
            "anomaly_count": len(anomalies),
        }

    # Build a brief summary
    total_anomalies = sum(m.get("anomaly_count", 0) for m in analysis["metrics"].values())
    analysis["summary"] = {"total_anomalies": total_anomalies}
    return analysis


def _summarize_metrics(analysis: Dict[str, Any]) -> str:
    total = analysis.get("summary", {}).get("total_anomalies", 0)
    if total == 0:
        return "No anomalies detected across provided metrics."
    parts = [f"Detected {total} anomalies across:"]
    for name, meta in analysis.get("metrics", {}).items():
        count = meta.get("anomaly_count", 0)
        if count:
            parts.append(f"- {name}: {count}")
    return "\n".join(parts)


# -------------------------
# Helpers: Design Review
# -------------------------

def _parse_architecture(input: str, context: Dict[str, Any]) -> Dict[str, Any]:
    # Accept JSON in input first, then fallback to context["architecture"].
    arch = _maybe_parse_json(input)
    if not isinstance(arch, dict):
        arch = context.get("architecture", {}) if isinstance(context, dict) else {}
    nodes = arch.get("nodes") or arch.get("services") or []
    connections = arch.get("connections") or arch.get("edges") or []
    return {"nodes": nodes, "connections": connections}


def _analyze_design(arch: Dict[str, Any]) -> Dict[str, Any]:
    nodes = arch.get("nodes", [])
    connections = arch.get("connections", [])

    # Build degree counts to detect SPOF candidates
    indegree: Dict[str, int] = {}
    outdegree: Dict[str, int] = {}
    for n in nodes:
        name = str(n.get("name") or n.get("id") or "")
        if name:
            indegree[name] = 0
            outdegree[name] = 0
    for c in connections:
        src = str(c.get("from") or c.get("source") or "")
        dst = str(c.get("to") or c.get("target") or "")
        if src in outdegree:
            outdegree[src] += 1
        if dst in indegree:
            indegree[dst] += 1

    # SPOF: nodes with high fan-in/out and no replicas/zone redundancy
    spofs: List[Dict[str, Any]] = []
    for n in nodes:
        name = str(n.get("name") or n.get("id") or "")
        replicas = int(n.get("replicas", 1))
        zones = n.get("zones") or n.get("az") or []
        critical = bool(n.get("critical", False))
        fan_in = indegree.get(name, 0)
        fan_out = outdegree.get(name, 0)
        if name and replicas <= 1 and (fan_in >= 2 or fan_out >= 2 or critical):
            spofs.append({
                "node": name,
                "replicas": replicas,
                "fan_in": fan_in,
                "fan_out": fan_out,
                "zones": zones,
                "reason": "Single replica with high dependency centrality or marked critical.",
            })

    # Redundancy improvements: suggest replicas and multi-AZ
    redundancy: List[Dict[str, Any]] = []
    for n in nodes:
        name = str(n.get("name") or n.get("id") or "")
        replicas = int(n.get("replicas", 1))
        zones = n.get("zones") or []
        suggestions: List[str] = []
        if replicas < 2:
            suggestions.append("Increase replicas to at least 2")
        if not zones or (isinstance(zones, list) and len(zones) < 2):
            suggestions.append("Distribute across >= 2 zones")
        if suggestions:
            redundancy.append({"node": name, "suggestions": suggestions})

    # Scalability risks: edges without async/queue, stateful services lacking sharding, DB with no read replicas
    scalability: List[Dict[str, Any]] = []
    for n in nodes:
        name = str(n.get("name") or n.get("id") or "")
        service_type = (n.get("type") or n.get("role") or "").lower()
        stateful = bool(n.get("stateful", service_type in {"db", "database", "cache"}))
        read_replicas = int(n.get("read_replicas", 0))
        shard_count = int(n.get("shards", 0))
        risks: List[str] = []
        if stateful and shard_count <= 1:
            risks.append("Stateful component lacks sharding")
        if service_type in {"db", "database"} and read_replicas < 1:
            risks.append("Database lacks read replicas")
        if risks:
            scalability.append({"node": name, "risks": risks})

    # Connection-level risks: synchronous chains and fan-in onto sync bottlenecks
    sync_risks: List[Dict[str, Any]] = []
    for c in connections:
        src = str(c.get("from") or c.get("source") or "")
        dst = str(c.get("to") or c.get("target") or "")
        mode = (c.get("mode") or c.get("protocol") or "sync").lower()
        if mode == "sync":
            sync_risks.append({"from": src, "to": dst, "reason": "Synchronous coupling may limit throughput"})

    return {
        "spofs": spofs,
        "redundancy": redundancy,
        "scalability": scalability,
        "connection_risks": sync_risks,
        "counts": {
            "spofs": len(spofs),
            "redundancy": len(redundancy),
            "scalability": len(scalability),
            "connection_risks": len(sync_risks),
        },
    }


def _summarize_design(analysis: Dict[str, Any]) -> str:
    c = analysis.get("counts", {})
    return (
        f"SPOFs: {c.get('spofs', 0)}, Redundancy suggestions: {c.get('redundancy', 0)}, "
        f"Scalability risks: {c.get('scalability', 0)}, Connection risks: {c.get('connection_risks', 0)}."
    )


def _extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    """Best-effort extraction of a JSON object from a model response."""
    # If already valid JSON
    obj = _maybe_parse_json(text)
    if isinstance(obj, dict):
        return obj
    # Try to find the first {...} block
    try:
        start = text.index("{")
        end = text.rindex("}")
        candidate = text[start : end + 1]
        obj = _maybe_parse_json(candidate)
        if isinstance(obj, dict):
            return obj
    except Exception:
        return None
    return None


def _build_postmortem_json(incident_input: str, root_cause: Dict[str, Any], timeline: List[Dict[str, Any]], extras: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "what_happened": incident_input,
        "impact": extras.get("impact") if extras else None,
        "root_cause": {
            "summary": root_cause.get("root_cause", "unknown"),
            "confidence": root_cause.get("confidence_score", 0.0),
            "explanation": root_cause.get("explanation", ""),
        },
        "mitigation": extras.get("mitigation") if extras else None,
        "action_items": extras.get("action_items") if extras else [],
        "timeline": timeline,
        "context": (extras or {}).get("context", {}),
    }


def _fallback_markdown_from_json(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# Postmortem")
    lines.append("")
    lines.append("## What Happened")
    lines.append(str(report.get("what_happened", "")))
    lines.append("")
    lines.append("## Impact")
    lines.append(str(report.get("impact", "Unknown")))
    lines.append("")
    lines.append("## Root Cause")
    rc = report.get("root_cause", {})
    lines.append(f"- Summary: {rc.get('summary', 'unknown')}")
    lines.append(f"- Confidence: {rc.get('confidence', 0.0)}")
    lines.append("")
    lines.append("## Mitigation")
    lines.append(str(report.get("mitigation", "TBD")))
    lines.append("")
    lines.append("## Action Items")
    for item in report.get("action_items", []) or []:
        lines.append(f"- {item}")
    if not report.get("action_items"):
        lines.append("- TBD")
    lines.append("")
    lines.append("## Timeline")
    for ev in report.get("timeline", []) or []:
        ts = ev.get("ts", "?")
        desc = ev.get("description", "")
        lines.append(f"- {ts}: {desc}")
    return "\n".join(lines)

