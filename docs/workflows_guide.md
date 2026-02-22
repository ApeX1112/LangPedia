# Workflow Guide

Workflows are the core concept in Langpedia. A workflow is a directed acyclic graph (DAG) of nodes that process data sequentially based on their dependencies.

## YAML Syntax

Workflows are defined in `.yaml` files inside the `workflows/` directory.

```yaml
name: "My RAG Pipeline"
version: "0.1"

nodes:
  - id: my_kb
    type: rag_retrieve
    inputs: ["input.query"]
    params:
      dataset_name: "knowledge_base"
      top_k: 5

  - id: summarizer
    type: llm
    inputs: ["my_kb.results"]
    params:
      prompt: "Summarize these documents: {results}"

edges:
  - source: my_kb
    target: summarizer
```

## Node Specification

Each node has:

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | ✅ | Unique identifier for this node |
| `type` | string | ✅ | Node type (must match a key in `NODE_REGISTRY` or falls back to placeholder) |
| `inputs` | list[string] | — | References to other nodes' outputs, e.g. `["input.query", "node_a.results"]` |
| `params` | dict | — | Configuration passed to the node at execution time |
| `scripts` | dict | — | Mapping of logical script names to file paths (auto-set by `generate-scripts`) |

### Input References

Inputs use dot notation: `<source_node_id>.<field>`.

- `input.query` — Reads the `query` field from the initial workflow input
- `my_kb.results` — Reads the `results` field from node `my_kb`'s output
- `my_kb` — Merges the entire output dict from `my_kb`

### Edge Derivation

If `edges` are omitted from the YAML, the API auto-derives them from `inputs` for Studio UI rendering.

## Available Node Types

| Type | Class | Description |
|---|---|---|
| `rag_retrieve` | `RAGRetrieveNode` | 3-phase pipeline: extract → vectorize → retrieve. Supports custom scripts. |

Unknown node types get a placeholder execution with a 0.5s delay.

## Custom Scripts

The `rag_retrieve` node supports user-defined Python scripts that follow the `NodeScript` interface:

```python
from backend.app.engine.nodes.base import NodeScript, NodeContext

class MyExtractor(NodeScript):
    def run(self, ctx: NodeContext, state: dict, config: dict) -> dict:
        ctx.emit("extract_start", {"info": "custom extraction"})
        # Your logic here
        return {"docs": ["doc1", "doc2"]}
```

**Lifecycle:** `validate(config)` → `run(ctx, state, config)` → `evaluate(ctx, before, after, config)`

Scripts are resolved in order:
1. Path defined in the YAML `scripts` mapping
2. `scripts/workflows/<workflow_name>/nodes/<node_id>/<script_name>.py`
3. `data/<dataset_name>/scripts/<script_name>.py`

Generate boilerplate with:
```bash
langpedia generate-scripts
```

## Execution

```bash
# Local execution
langpedia run workflows/my_pipeline.yaml --input '{"query": "What is AI?"}'

# Remote execution (requires running backend)
langpedia run workflows/my_pipeline.yaml --remote http://localhost:8000
```

The engine resolves dependencies, executes nodes in topological order, and logs events for every step. If a circular dependency is detected, execution halts with a deadlock error.
