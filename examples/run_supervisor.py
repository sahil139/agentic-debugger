from agentic_debugger import get_llm, SupervisorAgent


def main() -> None:
    llm = get_llm(model="gpt-oasis", temperature=0.2)
    supervisor = SupervisorAgent(llm)

    incident_input = "Checkout service returning 500s after deploy"
    context = {
        "service": "checkout",
        "env": "prod",
        "deploy_id": "abc123",
    }

    result = supervisor.run(incident_input, context)
    print("Combined Summary:\n")
    print(result.get("combined_summary", "<no summary>"))
    print("\nAgent Details:\n")
    for r in result.get("agents", []):
        print(f"[{r.get('agent')}]\n{r.get('summary','').strip()}\n")


if __name__ == "__main__":
    main()




