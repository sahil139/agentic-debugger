# Contributing to Agentic Debugger

Thank you for your interest in contributing to Agentic Debugger! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Git
- Basic understanding of AI/ML concepts

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/yourusername/agentic-debugger.git
   cd agentic-debugger
   ```

2. **Set up development environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Run tests to ensure everything works**
   ```bash
   python debugger.py --logs sample_app.log --metrics sample_metrics.csv --design sample_design.json
   ```

## 🛠️ Development Guidelines

### Code Style
- Follow PEP 8 Python style guidelines
- Use type hints for function parameters and return values
- Write docstrings for all public functions and classes
- Keep functions focused and single-purpose

### Testing
- Test your changes with sample data before submitting
- Ensure all agents work both with and without LLM connections
- Verify graceful error handling

### Agent Development

When adding new agents:

1. **Inherit from BaseAgent**
   ```python
   class NewAgent(BaseAgent):
       def __init__(self, llm):
           super().__init__(llm, name="NewAgent")
   ```

2. **Implement the run method**
   ```python
   def run(self, input: str, context: Dict[str, Any]) -> Dict[str, Any]:
       # Your analysis logic here
       return {
           "agent": self.name,
           "summary": "Brief summary",
           "details": {...}  # Structured data
       }
   ```

3. **Add to SupervisorAgent**
   - Update the `__init__` method
   - Add to the orchestration flow in `run`

### Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, documented code
   - Test thoroughly
   - Update documentation if needed

3. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add: Brief description of changes"
   ```

4. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## 📋 Issue Guidelines

### Bug Reports
When reporting bugs, please include:
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages/logs

### Feature Requests
For new features, please describe:
- Use case and motivation
- Proposed implementation approach
- Any breaking changes
- Examples of usage

## 🏗️ Project Structure

```
agentic_debugger/
├── agentic_debugger/          # Core package
│   ├── __init__.py           # Package exports
│   ├── base.py              # Base agent class
│   ├── agents.py            # Individual agents
│   ├── supervisor.py        # Orchestration
│   └── llm.py              # LLM integration
├── examples/                # Sample data and scripts
├── debugger.py             # CLI interface
├── download_model.py       # Model download utility
├── requirements.txt        # Dependencies
├── README.md              # Main documentation
├── CONTRIBUTING.md        # This file
└── LICENSE               # MIT License
```

## 🧪 Testing

### Manual Testing
```bash
# Test with sample data
python debugger.py --logs sample_app.log --metrics sample_metrics.csv --design sample_design.json

# Test individual components
python -c "from agentic_debugger import get_llm, LogAgent; print('LogAgent works!')"
```

### Test Data
- `sample_app.log`: Contains various log levels and stack traces
- `sample_metrics.csv`: Time-series data with anomalies
- `sample_design.json`: Simple architecture with SPOFs

## 📚 Documentation

### Code Documentation
- Use docstrings for all public functions
- Include type hints
- Add inline comments for complex logic

### README Updates
- Update feature lists when adding new agents
- Add usage examples for new functionality
- Keep installation instructions current

## 🐛 Common Issues

### LLM Connection Errors
- Ensure `GPOASIS_BASE_URL` is set correctly
- Check that local server is running
- Verify API key format

### Import Errors
- Make sure virtual environment is activated
- Run `pip install -r requirements.txt`
- Check Python version compatibility

## 💡 Ideas for Contributions

### New Agents
- **SecurityAgent**: Analyze security logs and vulnerabilities
- **PerformanceAgent**: Deep dive into performance metrics
- **DependencyAgent**: Analyze service dependencies and failures

### Improvements
- Better error handling and recovery
- More sophisticated anomaly detection
- Integration with monitoring systems (Prometheus, Grafana)
- Web UI for report visualization

### Documentation
- Video tutorials
- More detailed examples
- Integration guides for popular tools

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and ideas
- **Email**: your.email@example.com

## 🙏 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Project documentation

Thank you for contributing to Agentic Debugger! 🚀
