# Langpedia v0.1

All-in-one AI orchestration tool: agents + RAG + MCP tool access.

## Structure
- `/backend`: FastAPI backend.
- `/cli`: Python CLI tool.
- `/studio`: Next.js web application.
- `/shared`: Shared models and schemas.

## Getting Started

### CLI
```bash
pip install -e .
langpedia init
langpedia run workflows/starter.yaml
```

## 📖 Documentation
Detailed guides for scaling your AI projects:
- [Workflow Guide](docs/workflows_guide.md): Learn YAML syntax, data wiring, and project organization.

### Backend
```bash
pip install -r backend/requirements.txt
uvicorn backend.app.api.main:app --reload
```

### Studio
```bash
cd studio
npm install
npm run dev
```
