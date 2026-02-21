import typer
import yaml
import httpx
import asyncio
import os
import sys
from typing import Optional
from pathlib import Path
from rich import print 
from rich.console import Console

from rich.align import Align
from rich.markup import escape

console = Console()

# Using a more robust ASCII art style for terminal compatibility
BANNER_ART = r"""
   _                                       _ _       
  | |                                     | (_)      
  | |     __ _ _ __   __ _ _ __   ___   __| |_  __ _ 
  | |    / _` | '_ \ / _` | '_ \ / _ \ / _` | |/ _` |
  | |___| (_| | | | | (_| | |_) |  __/| (_| | | (_| |
  |______\__,_|_| |_|\__, | .__/ \___| \__,_|_|\__,_|
                      __/ | |                        
                     |___/|_|                        
"""

SUBTITLE = "AI Orchestration • Agents • RAG • MCP • Workflows"

# Fix imports for shared spec
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from shared.workflow import WorkflowSpec
from backend.app.engine.runner import WorkflowRunner

app = typer.Typer(
    help="Langpedia CLI - Advanced AI Orchestration Platform",
    rich_markup_mode="rich"
)

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    Langpedia CLI - Advanced AI Orchestration Platform.
    Use --help to see available commands.
    """
    if ctx.invoked_subcommand is None:
        # Render banner centered and escaped to prevent markup issues
        console.print(Align.center(f"[bold cyan]{escape(BANNER_ART)}[/bold cyan]"))
        console.print(Align.center(f"[italic blue]{SUBTITLE}[/italic blue]"))
        console.print("\n")
        console.print(Align.center("[dim]Version 0.1.0 • Local-first • Python-native[/dim]"))
        console.print(Align.center("[bold]Type [green]langpedia --help[/green] for instructions[/bold]"))
        console.print("\n")

@app.command()
def init(name: str = typer.Argument("my-langpedia-project", help="The name of your new project")):
    """Initialize a professional Langpedia workspace."""
    console.print(Align.center(f"[bold cyan]Initializing Langpedia Workspace: {name}...[/bold cyan]"))
    
    # 1. Create directory structure
    dirs = ["workflows", "data", "mcp", "logs"]
    for d in dirs:
        Path(d).mkdir(exist_ok=True)
        console.print(f"  [green]✔[/green] Created [bold]{d}/[/bold]")

    # 2. Create starter workflow
    workflow_filename = f"{name.lower().replace(' ', '_')}.yaml"
    starter_wf = {
        "name": name,
        "version": "0.1",
        "nodes": [
            {
                "id": "starter_node",
                "type": "llm",
                "params": {"prompt": f"Welcome to {name}!"}
            }
        ],
        "edges": []
    }
    
    workflow_path = Path("workflows") / workflow_filename
    with open(workflow_path, "w") as f:
        yaml.dump(starter_wf, f)
    console.print(f"  [green]✔[/green] Created [bold]workflows/{workflow_filename}[/bold]")

    # 3. Synchronize with UI/Backend if running
    API_URL = "http://localhost:8000/workflows/"
    try:
        # We use a short timeout so we don't hang if the server isn't there
        res = httpx.post(API_URL, json=starter_wf, timeout=2.0)
        if res.status_code == 200:
            console.print(f"  [green]✔[/green] Synchronized [bold]{name}[/bold] with Studio UI")
    except Exception:
        # Silently fail if server isn't running, this is just a convenience
        console.print("  [yellow]![/yellow] [dim]Studio Backend not found. Run 'uvicorn' to sync later.[/dim]")

    # 4. Create .env.example
    with open(".env.example", "w") as f:
        f.write("# Langpedia Environment Configuration\n")
        f.write("OPENAI_API_KEY=your_key_here\n")
        f.write("ANTHROPIC_API_KEY=your_key_here\n")
        f.write("QDRANT_URL=http://localhost:6333\n")
    console.print("  [green]✔[/green] Created [bold].env.example[/bold]")

    console.print("\n[bold green]Success![/bold green] Your Langpedia workspace is ready.")
    console.print("Next steps:")
    console.print("1. [dim]Rename .env.example to .env and add your keys.[/dim]")
    console.print("2. [dim]Run your first workflow:[/dim] [bold yellow]langpedia run workflows/starter.yaml[/]")

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
