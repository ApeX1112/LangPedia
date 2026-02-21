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
langpedia run samples/rag_qa.yaml
```

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
