# Langpedia v0.1

All-in-one AI orchestration tool: agents + RAG + MCP tool access.

## Structure

```
├── backend/          # FastAPI backend + execution engine
├── cli/              # Python CLI tool (typer + rich)
├── studio/           # Next.js web application (React Flow)
├── shared/           # Shared Pydantic models and schemas
├── tests/            # Pytest test suite + run scripts
├── .github/workflows # CI pipeline (lint + test)
├── clean_install.ps1 # Windows setup script
└── clean_install.sh  # Linux/macOS setup script
```

## Getting Started

### Quick Setup (recommended)

**Windows:**
```powershell
.\clean_install.ps1
```

**Linux / macOS:**
```bash
chmod +x clean_install.sh
./clean_install.sh
```

This creates a `.venv-langpedia` virtual environment, installs all Python and Node dependencies, and sets up pre-commit hooks.

### Manual Setup

```bash
python -m venv .venv-langpedia
source .venv-langpedia/bin/activate   # Linux/macOS
# .\.venv-langpedia\Scripts\Activate.ps1   # Windows

pip install -e ".[dev]"
pre-commit install
cd studio && npm install
```

### Running Services

```bash
# Backend API
uvicorn backend.app.api.main:app --reload

# Studio UI
cd studio && npm run dev

# CLI
langpedia init
langpedia run workflows/starter.yaml
```

## Testing & Quality

### Run Tests
```powershell
# Windows
.\tests\run_tests.ps1

# Linux / macOS
bash tests/run_tests.sh
```

### Linting
```bash
pre-commit run --all-files    # Run all hooks
ruff check .                  # Lint only
ruff format --check .         # Format check only
```


## Documentation
- [Architecture](docs/architecture.md): Components, data flow, and synchronization model.
- [API Reference](docs/api.md): REST endpoints with request/response examples.
- [CLI Reference](docs/cli.md): All 8 CLI commands with options.
- [Workflow Guide](docs/workflows_guide.md): YAML syntax, node specs, and custom scripts.
- [Development](docs/development.md): Setup, testing, CI, and extending the platform.
