import argparse
import csv
import json
import os
from typing import Any, Dict, List

from agentic_debugger import get_llm, SupervisorAgent


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def load_metrics_csv(path: str) -> Dict[str, List[Dict[str, Any]]]:
    metrics: Dict[str, List[Dict[str, Any]]] = {}
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            metric = str(row.get("metric") or row.get("name") or "default")
            ts = row.get("ts") or row.get("timestamp") or row.get("time")
            try:
                value = float(row.get("value"))
            except Exception:
                continue
            metrics.setdefault(metric, []).append({"ts": ts, "value": value})
    return metrics


def load_design_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return json.load(f)


def write_file(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8", errors="replace") as f:
        f.write(content)


def to_design_markdown(design_details: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# Design Review")
    lines.append("")
    c = (design_details.get("counts") or {})
    lines.append(
        f"Findings: SPOFs={c.get('spofs', 0)}, Redundancy={c.get('redundancy', 0)}, "
        f"Scalability={c.get('scalability', 0)}, Connection Risks={c.get('connection_risks', 0)}"
    )
    lines.append("")
    if design_details.get("explanation"):
        lines.append("## Summary")
        lines.append(str(design_details.get("explanation")))
        lines.append("")
    if design_details.get("spofs"):
        lines.append("## Single Points of Failure")
        for item in design_details.get("spofs", []) or []:
            lines.append(
                f"- {item.get('node')} (replicas={item.get('replicas')}, fan_in={item.get('fan_in')}, fan_out={item.get('fan_out')})"
            )
        lines.append("")
    if design_details.get("redundancy"):
        lines.append("## Redundancy Improvements")
        for item in design_details.get("redundancy", []) or []:
            node = item.get("node")
            for s in item.get("suggestions", []) or []:
                lines.append(f"- {node}: {s}")
        lines.append("")
    if design_details.get("scalability"):
        lines.append("## Scalability Risks")
        for item in design_details.get("scalability", []) or []:
            node = item.get("node")
            for r in item.get("risks", []) or []:
                lines.append(f"- {node}: {r}")
        lines.append("")
    if design_details.get("connection_risks"):
        lines.append("## Connection Risks")
        for item in design_details.get("connection_risks", []) or []:
            lines.append(f"- {item.get('from')} -> {item.get('to')}: {item.get('reason')}")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run agentic debugger and produce RCA outputs.")
    parser.add_argument("--logs", required=True, help="Path to logs file")
    parser.add_argument("--metrics", required=False, help="Path to metrics CSV (metric,ts,value)")
    parser.add_argument("--design", required=False, help="Path to design JSON (nodes, connections)")
    parser.add_argument("--model", default="gpt-oasis", help="Model name for local LLM")
    parser.add_argument("--temperature", type=float, default=0.2, help="LLM temperature")
    parser.add_argument("--outdir", default=".", help="Output directory")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    # Build context
    context: Dict[str, Any] = {}
    if args.metrics and os.path.isfile(args.metrics):
        context["metrics"] = load_metrics_csv(args.metrics)
    if args.design and os.path.isfile(args.design):
        context["architecture"] = load_design_json(args.design)

    # Input for supervisor: pass the logs path (LogAgent will read file or treat as text)
    incident_input = args.logs

    llm = get_llm(model=args.model, temperature=args.temperature)
    supervisor = SupervisorAgent(llm)
    result = supervisor.run(incident_input, context)

    # Write RCA.json (full consolidated output)
    rca_json_path = os.path.join(args.outdir, "RCA.json")
    write_file(rca_json_path, json.dumps(result, indent=2))

    # Write RCA.md (top-level consolidated markdown)
    rca_md_path = os.path.join(args.outdir, "RCA.md")
    write_file(rca_md_path, str(result.get("markdown_report", "")))

    # Write DesignReview.md from DesignReviewAgent details if present
    design = next((r for r in result.get("agents", []) if r.get("agent") == "DesignReviewAgent"), None)
    design_details = (design.get("details") if design else {}) or {}
    design_md_path = os.path.join(args.outdir, "DesignReview.md")
    write_file(design_md_path, to_design_markdown(design_details))

    print(f"Wrote: {rca_json_path}\nWrote: {rca_md_path}\nWrote: {design_md_path}")


if __name__ == "__main__":
    main()




