from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

# Import shared spec
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from backend.app.models.database import SessionLocal, init_db, Workflow, Run, Trace
from backend.app.engine.runner import WorkflowRunner
from shared.workflow import WorkflowSpec

app = FastAPI(title="Langpedia API", version="0.1")

@app.on_event("startup")
def on_startup():
    init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from fastapi import Depends
from sqlalchemy.orm import Session

@app.get("/")
async def root():
    return {"message": "Welcome to Langpedia API v0.1"}

@app.post("/workflows/")
async def create_workflow(workflow_spec: WorkflowSpec, db: Session = Depends(get_db)):
    workflow_id = str(uuid.uuid4())
    db_workflow = Workflow(
        id=workflow_id,
        name=workflow_spec.name,
        spec=workflow_spec.dict()
    )
    db.add(db_workflow)
    db.commit()
    return {"id": workflow_id, "status": "created"}

@app.post("/runs/")
async def run_workflow(workflow_id: str, initial_input: Dict[str, Any], db: Session = Depends(get_db)):
    db_workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not db_workflow:
        return {"error": "Workflow not found"}
    
    spec = WorkflowSpec(**db_workflow.spec)
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
