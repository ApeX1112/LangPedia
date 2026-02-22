# Development Guide

## Setup

```bash
# Windows
.\clean_install.ps1

# Linux / macOS
chmod +x clean_install.sh
./clean_install.sh
```

This creates `.venv-langpedia`, installs all dependencies, sets up pre-commit hooks, and installs Studio's Node modules.

## Project Structure

```
langpedia/
├── backend/
│   └── app/
│       ├── api/main.py          # FastAPI application (6 endpoints)
│       ├── engine/
│       │   ├── runner.py        # WorkflowRunner (DAG executor)
│       │   └── nodes/
│       │       ├── base.py      # BaseNode, NodeContext, NodeScript
│       │       ├── rag_node.py  # RAGRetrieveNode implementation
│       │       └── registry.py  # NODE_REGISTRY mapping
│       └── models/
│           └── database.py      # SQLAlchemy models (Workflow, Run, Trace)
├── cli/
│   └── langpedia/
│       └── main.py              # Typer CLI (8 commands)
├── shared/
│   └── workflow.py              # Pydantic models (WorkflowSpec, NodeSpec, EdgeSpec)
├── studio/
│   └── src/
│       ├── app/page.tsx         # Next.js dashboard
│       └── components/
│           └── WorkflowCanvas.tsx # React Flow canvas
├── tests/
│   ├── conftest.py              # Shared fixtures
│   ├── run_tests.ps1            # Windows test runner
│   ├── run_tests.sh             # Linux/macOS test runner
│   ├── test_shared/             # Pydantic model tests
│   └── test_backend/            # Engine, API, DB, node tests
├── docs/                        # Project documentation
├── clean_install.ps1            # Windows setup
├── clean_install.sh             # Linux/macOS setup
├── pyproject.toml               # Dependencies, ruff, pytest config
└── .pre-commit-config.yaml      # Pre-commit hooks
```

## Running Services

```bash
# Backend API (http://localhost:8000)
uvicorn backend.app.api.main:app --reload

# Studio UI (http://localhost:3000)
cd studio && npm run dev
```

## Testing

```powershell
# Windows
.\tests\run_tests.ps1
.\tests\run_tests.ps1 -Verbose                 # Show print output
.\tests\run_tests.ps1 -Filter "test_runner"     # Filter by name
```

```bash
# Linux / macOS
bash tests/run_tests.sh
bash tests/run_tests.sh -v                      # Show print output
bash tests/run_tests.sh -k "test_runner"         # Filter by name
```

### Test Layout

| Module | Coverage |
|---|---|
| `test_shared/test_workflow.py` | Pydantic models: creation, validation, serialization |
| `test_backend/test_runner.py` | DAG execution, dependency resolution, deadlock detection |
| `test_backend/test_nodes.py` | BaseNode, NodeContext, NodeScript, NODE_REGISTRY |
| `test_backend/test_database.py` | Table creation, CRUD, foreign keys, timestamps |
| `test_backend/test_api.py` | FastAPI endpoints via TestClient |

## Code Quality

### Pre-commit Hooks

Runs automatically on `git commit`:
- **ruff** — lint + format (replaces black + isort + flake8)
- **trailing-whitespace** / **end-of-file-fixer** / **check-yaml** / **check-added-large-files**

```bash
pre-commit run --all-files    # Run manually
```

### Ruff Config (in `pyproject.toml`)

- Target: Python 3.11
- Line length: 120
- Rules: `E` (pycodestyle), `F` (pyflakes), `I` (isort), `W` (warnings), `UP` (pyupgrade)

### CI Pipeline

GitHub Actions (`.github/workflows/ci.yml`) runs on every push/PR to `main`:

1. **Lint** — `ruff check` + `ruff format --check`
2. **Test** — `pip install -e ".[dev]"` → `bash tests/run_tests.sh`

## Adding a New Node Type

1. Create `backend/app/engine/nodes/my_node.py`:

```python
from .base import BaseNode
from typing import Any, Dict

class MyNode(BaseNode):
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        self.log("Running my custom logic")
        result = input_data.get("text", "").upper()
        return {"result": result}
```

2. Register in `backend/app/engine/nodes/registry.py`:

```python
from .my_node import MyNode

NODE_REGISTRY: Dict[str, Type[BaseNode]] = {
    "rag_retrieve": RAGRetrieveNode,
    "my_node": MyNode,
}
```

3. Use in a workflow YAML:

```yaml
nodes:
  - id: transformer
    type: my_node
    inputs: ["input.text"]
```
