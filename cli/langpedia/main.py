import typer
import yaml
import httpx
import asyncio
import os
import sys
from typing import Optional
from pathlib import Path

# Fix imports for shared spec
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from shared.workflow import WorkflowSpec
from backend.app.engine.runner import WorkflowRunner

app = typer.Typer(help="Langpedia CLI - AI Orchestration Tool")

@app.command()
def init():
    """Initialize a new Langpedia project."""
    typer.echo("Initializing Langpedia project...")
    Path("workflows").mkdir(exist_ok=True)
    with open("langpedia.yaml", "w") as f:
        f.write("project_name: my-langpedia-project\n")
    typer.echo("Done.")

@app.command()
def run(
    file: str,
    input: str = typer.Option("{}", "--input", "-i", help="JSON input for the workflow"),
    remote: Optional[str] = typer.Option(None, "--remote", "-r", help="Remote server URL"),
    local: bool = typer.Option(True, "--local", "-l", help="Run locally (default)")
):
    """Run a workflow from a YAML file."""
    import json
    input_data = json.loads(input)
    
    if remote:
        typer.echo(f"Running workflow {file} remotely on {remote}...")
        # TODO: Implement remote call
        async def run_remote():
            async with httpx.AsyncClient() as client:
                # 1. Create/Upload workflow
                with open(file, 'r') as f:
                    spec_data = yaml.safe_load(f)
                resp = await client.post(f"{remote}/workflows/", json=spec_data)
                workflow_id = resp.json().get("id")
                
                # 2. Run it
                resp = await client.post(f"{remote}/runs/", params={"workflow_id": workflow_id}, json=input_data)
                typer.echo(f"Run output: {resp.json().get('outputs')}")
        
        asyncio.run(run_remote())
    else:
        typer.echo(f"Running workflow {file} locally...")
        with open(file, 'r') as f:
            spec_data = yaml.safe_load(f)
        
        spec = WorkflowSpec(**spec_data)
        runner = WorkflowRunner(spec)
        
        outputs = asyncio.run(runner.run(input_data))
        typer.echo(f"Execution successful!")
        typer.echo(f"Outputs: {outputs}")

@app.command()
def rag_ingest(path: str):
    """Ingest documents into the RAG system."""
    typer.echo(f"Ingesting documents from {path}...")
    # Mock for v0.1
    typer.echo("Ingestion complete (Mocked).")

@app.command()
def mcp_add(name: str, url: str):
    """Add an MCP server."""
    typer.echo(f"Adding MCP server {name} at {url}...")
    # Mock for v0.1
    typer.echo("MCP server added (Mocked).")

if __name__ == "__main__":
    app()
