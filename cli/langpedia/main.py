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
