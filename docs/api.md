# API Reference

Base URL: `http://localhost:8000`

Start the server:
```bash
uvicorn backend.app.api.main:app --reload
```

## Endpoints

### `GET /`

Health check.

**Response:**
```json
{ "message": "Welcome to Langpedia API v0.1" }
```

---

### `GET /workflows/`

List all workflows from the filesystem and database. Local YAML files take priority (de-duplicated by name).

**Response:**
```json
[
  {
    "id": "file:my_workflow.yaml",
    "name": "My Workflow (Local)",
    "spec": { "version": "0.1", "name": "My Workflow", "nodes": [...], "edges": [...] },
    "source": "file"
  },
  {
    "id": "uuid-string",
    "name": "DB Workflow",
    "spec": { ... },
    "source": "db"
  }
]
```

> [!NOTE]
> The API auto-derives `edges` from node `inputs` fields if edges are missing from the YAML file.

---

### `POST /workflows/`

Create a new workflow (saved to database).

**Request Body:**
```json
{
  "name": "My Workflow",
  "version": "0.1",
  "nodes": [
    { "id": "node_1", "type": "llm", "inputs": [], "params": { "prompt": "Hello" } }
  ],
  "edges": []
}
```

**Response:**
```json
{ "id": "generated-uuid", "status": "created" }
```

---

### `GET /workflows/{workflow_id}`

Get a single workflow by ID. Supports both file-based IDs (`file:name.yaml`) and database UUIDs.

**Response:**
```json
{ "id": "...", "name": "...", "spec": { ... }, "source": "file" | "db" }
```

---

### `POST /runs/`

Execute a workflow and record the run.

**Query Parameters:**
- `workflow_id` — ID of the workflow to run

**Request Body:**
```json
{ "text": "Hello from the user" }
```

**Response:**
```json
{
  "run_id": "generated-uuid",
  "outputs": {
    "input": { "text": "Hello from the user" },
    "node_1": { "status": "success", "message": "..." }
  }
}
```

The run is recorded in the `runs` table and a trace of all events is saved to the `traces` table.
