import asyncio
import json
import os
import sys
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import yaml
from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.engine.runner import WorkflowRunner
from backend.app.models.database import Run, SessionLocal, Trace, Workflow, init_db
from shared.workflow import WorkflowSpec


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize the database
    init_db()
    yield
    # Shutdown: No cleanup needed for now


app = FastAPI(title="Langpedia API", version="0.1", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_headers=["*"],
    allow_methods=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
async def root():
    return {"message": "Welcome to Langpedia API v0.1"}


@app.post("/workflows/")
async def create_workflow(workflow_spec: WorkflowSpec, db: Session = Depends(get_db)):
    workflow_id = str(uuid.uuid4())
    db_workflow = Workflow(id=workflow_id, name=workflow_spec.name, spec=workflow_spec.model_dump())
    db.add(db_workflow)
    db.commit()
    return {"id": workflow_id, "status": "created"}


WORKFLOWS_DIR = Path("workflows")


@app.get("/workflows/")
async def list_workflows(db: Session = Depends(get_db)):
    # 1. Get from Filesystem (Source of truth for local)
    results = []
    seen_names = set()

    if WORKFLOWS_DIR.exists():
        for f in WORKFLOWS_DIR.glob("*.yaml"):
            try:
                with open(f) as wf:
                    data = yaml.safe_load(wf)
                    name = data.get("name", f.name)
                    # Derive edges for UI if missing
                    if "edges" not in data or not data["edges"]:
                        data["edges"] = []
                        for node in data.get("nodes", []):
                            for input_ref in node.get("inputs", []):
                                source_id = input_ref.split(".")[0]
                                if source_id != "input":
                                    data["edges"].append({"source": source_id, "target": node["id"]})

                    results.append({"id": f"file:{f.name}", "name": f"{name} (Local)", "spec": data, "source": "file"})
                    seen_names.add(name)
            except Exception as e:
                print(f"Error loading {f}: {e}")

    # 2. Get from Database (Only if not already seen in filesystem)
    db_workflows = db.query(Workflow).all()
    for w in db_workflows:
        if w.name not in seen_names:
            results.append({"id": w.id, "name": w.name, "spec": w.spec, "source": "db"})

    return results


@app.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str, db: Session = Depends(get_db)):
    # Check if it's a file-based workflow
    if workflow_id.startswith("file:"):
        filename = workflow_id.replace("file:", "")
        path = WORKFLOWS_DIR / filename
        if path.exists():
            with open(path) as f:
                data = yaml.safe_load(f)
                # Ensure edges are present for UI
                if "edges" not in data or not data["edges"]:
                    data["edges"] = []
                    for node in data.get("nodes", []):
                        for input_ref in node.get("inputs", []):
                            source_id = input_ref.split(".")[0]
                            if source_id != "input":
                                data["edges"].append({"source": source_id, "target": node["id"]})
                return {"id": workflow_id, "name": data.get("name"), "spec": data, "source": "file"}

    # Check database
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        return {"error": "Workflow not found"}
    return workflow


from fastapi.responses import StreamingResponse
import json

@app.post("/runs/")
async def run_workflow(workflow_id: str, initial_input: dict[str, Any], db: Session = Depends(get_db)):
    spec_data = None

    if workflow_id.startswith("file:"):
        filename = workflow_id.replace("file:", "")
        path = WORKFLOWS_DIR / filename
        if path.exists():
            with open(path) as f:
                spec_data = yaml.safe_load(f)
    else:
        db_workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if db_workflow:
            spec_data = db_workflow.spec

    if not spec_data:
        return {"error": "Workflow not found"}

    spec = WorkflowSpec(**spec_data)
    runner = WorkflowRunner(spec)

    run_id = str(uuid.uuid4())
    db_run = Run(id=run_id, workflow_id=workflow_id, status="running")
    db.add(db_run)
    db.commit()

    # Run in background or wait for MVP
    outputs = await runner.run(initial_input)

    db_run.status = "completed"
    db_trace = Trace(id=str(uuid.uuid4()), run_id=run_id, events=runner.events)
    db.add(db_trace)
    db.commit()

    return {"run_id": run_id, "outputs": outputs}

# Removed manual OPTIONS handler as CORSMiddleware handles pre-flight requests automatically.

@app.get("/runs/stream")
async def stream_workflow(request: Request, workflow_id: str, db: Session = Depends(get_db)):
    spec_data = None
    if workflow_id.startswith("file:"):
        filename = workflow_id.replace("file:", "")
        path = WORKFLOWS_DIR / filename
        if path.exists():
            with open(path) as f:
                spec_data = yaml.safe_load(f)
    else:
        db_workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if db_workflow:
            spec_data = db_workflow.spec

    if not spec_data:
        return {"error": "Workflow not found"}

    queue = asyncio.Queue()

    def stream_event_handler(event_type: str, data: dict[str, Any]):
        queue.put_nowait({"type": event_type, "data": data})

    spec = WorkflowSpec(**spec_data)
    runner = WorkflowRunner(spec, on_event=stream_event_handler)

    async def event_generator():
        # Start execution in the background
        execution_task = asyncio.create_task(runner.run({}))
        
        try:
            while True:
                # Wait for next event or completion of the runner task
                event_task = asyncio.create_task(queue.get())
                done, pending = await asyncio.wait(
                    [event_task, execution_task],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                if await request.is_disconnected():
                    break
                    
                if event_task in done:
                    event = event_task.result()
                    yield f"data: {json.dumps(event)}\n\n"
                    # Exit loop if it's the final event
                    if event["type"] in ["workflow_end", "workflow_error"]:
                        break
                elif execution_task in done:
                    # Runner finished but might have flushed final events to queue
                    if not queue.empty():
                        while not queue.empty():
                            event = queue.get_nowait()
                            yield f"data: {json.dumps(event)}\n\n"
                    break
        finally:
            execution_task.cancel()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )
