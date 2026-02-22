# CLI Reference

The `langpedia` CLI is built with [Typer](https://typer.tiangolo.com/) and [Rich](https://rich.readthedocs.io/).

```bash
pip install -e ".[dev]"
langpedia --help
```

## Commands

### `langpedia init [NAME]`

Initialize a new workspace. Creates the project directory structure, a starter YAML workflow, and a `.env.example` file. Optionally syncs with the Studio backend if it's running.

```bash
langpedia init my-project
```

**Creates:** `workflows/`, `data/`, `mcp/`, `logs/`, `scripts/`, `.env.example`, and a starter workflow YAML.

---

### `langpedia use <FILE>`

Set a workflow as the active default for subsequent commands. Stores the path in `.langpedia_state`.

```bash
langpedia use workflows/my_workflow.yaml
```

---

### `langpedia run [FILE] [OPTIONS]`

Execute a workflow. Uses the active workflow if no file is specified.

| Option | Default | Description |
|---|---|---|
| `--input`, `-i` | `{}` | JSON string passed as initial input |
| `--remote`, `-r` | `None` | URL of remote backend (posts spec + runs remotely) |
| `--local`, `-l` | `True` | Run locally using `WorkflowRunner` |

```bash
langpedia run workflows/rag.yaml --input '{"query": "What is AI?"}'
langpedia run --remote http://my-server:8000
```

---

### `langpedia list`

List all `.yaml` workflows in the `workflows/` directory. Shows which one is currently active (⭐).

---

### `langpedia generate-scripts [NODE_ID] [WORKFLOW_PATH]`

Generate boilerplate Python scripts for supported node types (currently `rag_retrieve`). Scripts are placed in `scripts/workflows/<name>/nodes/<node_id>/`. The workflow YAML is updated with script path mappings.

```bash
langpedia generate-scripts          # All nodes in active workflow
langpedia generate-scripts my_kb    # Specific node
```

---

### `langpedia sync [OPTIONS]`

Push all local workflows to the Studio backend.

| Option | Default | Description |
|---|---|---|
| `--remote`, `-r` | `http://localhost:8000` | Backend URL |

---

### `langpedia rag-ingest <PATH>`

Ingest documents into the RAG system. *(Mocked in v0.1)*

---

### `langpedia mcp-add <NAME> <URL>`

Register an MCP tool server. *(Mocked in v0.1)*
