# Langpedia YAML Workflow Guide

This guide explains how to build, organize, and scale your AI orchestrations using Langpedia YAML files.

## 核心概念 (Core Concepts)

A workflow is a **Directed Acyclic Graph (DAG)**. Each node perform a specific task and passes its data to the next node.

### 1. Basic Structure
Every workflow file requires a `name`, `version`, and a list of `nodes`.

```yaml
name: "My Story Generator"
version: "0.1"
nodes:
  - id: "prompt_creator"
    type: "llm"
    params:
      prompt: "Write a story about a cat."
```

### 2. Inputs and Data Flow
The power of YAML workflows comes from **Data Wiring**. You can use the output of one node as the input for another.

**Syntax**: `id.field` (e.g., `writer.text`)

```yaml
nodes:
  - id: "idea_generator"
    type: "llm"
    params:
      prompt: "Give me a unique story premise."
      
  - id: "writer"
    type: "llm"
    inputs: ["idea_generator.output"] # Connects output of 'idea_generator' to this node
    params:
      prompt: "Expand this premise into a short story: {{idea_generator.output}}"
```

### 3. Node Types (v0.1)
| Type | Description | Key Params |
| :--- | :--- | :--- |
| `llm` | AI Text Generation | `prompt`, `model`, `temperature` |
| `rag` | Retrieve Documents | `query`, `collection`, `limit` |
| `tool` | Call an MCP Tool | `tool_name`, `arguments` |
| `python` | Custom Logic | `code_snippet`, `function_name` |

---

## 📂 Organizing Large Workflows

As your project grows, follow these best practices:

### Atomic Nodes
Keep each node focused on **one thing**. Instead of one giant prompt, use three nodes: `Research` -> `Plan` -> `Write`.

### Naming Conventions
Use descriptive IDs.
- ❌ `node_1`, `node_2`
- ✅ `user_intent_parser`, `vector_search`, `final_response_author`

### Multi-File Strategy
For very complex systems, split your logic into multiple YAML files and use the `langpedia run` command to trigger them sequentially or as sub-workflows (coming in v0.2).

---

## 💻 Syncing with the Studio UI
When you use `langpedia init`, your workflow is saved locally. To see it in the UI and access its execution history:
1. Ensure `uvicorn` is running.
2. Run `langpedia run workflows/your_file.yaml --remote http://localhost:8000`.
3. The UI will automatically detect the new "Run" and the workflow schema, making it editable in the visual canvas.
