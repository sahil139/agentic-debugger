# Agentic Debugger

An intelligent incident analysis system that uses specialized AI agents to analyze logs, metrics, and system architecture to provide comprehensive root cause analysis and postmortem reports.

## 🚀 Features

- **Multi-Agent Architecture**: Specialized agents for different analysis tasks
- **Parallel Processing**: Log and metrics analysis run concurrently for speed
- **Structured Output**: JSON and Markdown reports for both humans and systems
- **Local LLM Support**: Works with local models via OpenAI-compatible APIs
- **Graceful Degradation**: Continues working even when LLM services are unavailable

## 🤖 Agents

| Agent | Purpose | Output |
|-------|---------|--------|
| **LogAgent** | Parses log files, extracts errors, anomalies, and stack traces | Structured JSON with error counts and details |
| **MetricsAgent** | Detects anomalies in time-series metrics using z-score analysis | Anomaly detection with statistical confidence |
| **DesignReviewAgent** | Analyzes system architecture for SPOFs and scalability issues | Design recommendations and risk assessment |
| **RootCauseAgent** | Correlates findings from other agents to identify root causes | Root cause hypothesis with confidence scores |
| **PostmortemAgent** | Generates comprehensive incident reports | Both JSON and Markdown postmortem documents |
| **SupervisorAgent** | Orchestrates all agents and consolidates outputs | Unified analysis report |

## 📦 Installation

### Prerequisites
- Python 3.9+
- Git

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/agentic-debugger.git
   cd agentic-debugger
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download model (optional)**
   ```bash
   python download_model.py --repo-id openai/gpt-oss-20b
   ```

## 🚀 Quick Start

### Basic Usage

```bash
python debugger.py --logs app.log --metrics metrics.csv --design architecture.json --outdir ./output
```

### With Sample Data

```bash
python debugger.py --logs sample_app.log --metrics sample_metrics.csv --design sample_design.json --outdir ./output
```

## 📊 Input Formats

### Log Files
Any text-based log file. The system automatically detects:
- Error messages (ERROR, FATAL, CRITICAL)
- Stack traces
- Anomalous patterns (timeouts, connection issues)

### Metrics CSV
```csv
metric,ts,value
cpu,1,0.20
cpu,2,0.25
latency_ms,1,120
latency_ms,2,130
throughput_rps,1,1000
throughput_rps,2,990
```

### Architecture JSON
```json
{
  "nodes": [
    {"name": "api", "replicas": 1, "zones": ["az1"], "type": "service"},
    {"name": "db", "replicas": 1, "type": "db", "read_replicas": 0, "stateful": true}
  ],
  "connections": [
    {"from": "api", "to": "db", "mode": "sync"}
  ]
}
```

## 📁 Output Files

The system generates three main outputs:

- **`RCA.json`**: Complete structured data from all agents
- **`RCA.md`**: Human-readable incident report
- **`DesignReview.md`**: System architecture recommendations

## ⚙️ Configuration

### Environment Variables

```bash
# Local LLM Configuration
export GPOASIS_BASE_URL="http://localhost:8080/v1"
export GPOASIS_API_KEY="sk-no-key"

# Model Download (optional)
export GPOASIS_REPO_ID="openai/gpt-oss-20b"
export GPOASIS_REVISION="main"
```

### CLI Options

```bash
python debugger.py --help

Options:
  --logs PATH           Path to log file (required)
  --metrics PATH        Path to metrics CSV (optional)
  --design PATH         Path to architecture JSON (optional)
  --model TEXT          Model name for local LLM [default: gpt-oasis]
  --temperature FLOAT   LLM temperature [default: 0.2]
  --outdir PATH         Output directory [default: .]
```

## 🏗️ Architecture

```
agentic_debugger/
├── agentic_debugger/          # Core package
│   ├── __init__.py
│   ├── base.py               # Base agent class
│   ├── agents.py             # Individual agent implementations
│   ├── supervisor.py         # Orchestration logic
│   └── llm.py               # LLM factory
├── examples/                 # Sample data and scripts
├── debugger.py              # CLI interface
├── download_model.py        # Model download utility
├── requirements.txt         # Dependencies
└── README.md               # This file
```

## 🔧 Development

### Running Tests

```bash
# Test with sample data
python debugger.py --logs sample_app.log --metrics sample_metrics.csv --design sample_design.json

# Test individual agents
python -c "from agentic_debugger import get_llm, LogAgent; print('Testing LogAgent...')"
```

### Adding New Agents

1. Inherit from `BaseAgent`
2. Implement the `run(input: str, context: dict) -> dict` method
3. Add to `SupervisorAgent` orchestration

Example:
```python
class CustomAgent(BaseAgent):
    def __init__(self, llm):
        super().__init__(llm, name="CustomAgent")
    
    def run(self, input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        # Your analysis logic here
        return {"agent": self.name, "summary": "...", "details": {...}}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [LangChain](https://github.com/langchain-ai/langchain) for LLM integration
- Uses [Hugging Face Hub](https://github.com/huggingface/huggingface_hub) for model management
- Inspired by modern SRE practices and incident response workflows
