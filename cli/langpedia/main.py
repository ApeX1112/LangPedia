import asyncio
import json
import os
import sys
import time
from pathlib import Path

import httpx
import typer
import yaml
from rich.align import Align
from rich.console import Console, Group
from rich.markup import escape
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from backend.app.engine.runner import WorkflowRunner  # noqa: E402
from shared.workflow import WorkflowSpec  # noqa: E402

STATE_FILE = ".langpedia_state"


def get_current_workflow():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f).get("current_workflow")
    return None


def set_current_workflow(path: str):
    with open(STATE_FILE, "w") as f:
        json.dump({"current_workflow": path}, f)


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


app = typer.Typer(help="Langpedia CLI - Advanced AI Orchestration Platform", rich_markup_mode="rich")


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
    dirs = ["workflows", "data", "mcp", "logs", "scripts"]
    for d in dirs:
        Path(d).mkdir(exist_ok=True)
        console.print(f"  [green]✔[/green] Created [bold]{d}/[/bold]")

    # Also create scripts/workflows/
    (Path("scripts") / "workflows").mkdir(exist_ok=True)

    # 2. Create starter workflow
    workflow_filename = f"{name.lower().replace(' ', '_')}.yaml"
    starter_wf = {
        "name": name,
        "version": "0.1",
        "nodes": [{"id": "starter_node", "type": "llm", "params": {"prompt": f"Welcome to {name}!"}}],
        "edges": [],
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
    console.print(f"2. [dim]Set active workflow:[/dim] [bold yellow]langpedia use workflows/{workflow_filename}[/]")
    console.print("3. [dim]Run it:[/dim] [bold yellow]langpedia run[/]")


@app.command()
def generate_scripts(
    node_id: str | None = typer.Argument(
        None, help="The ID of the node to generate scripts for. If omitted, generates for all nodes."
    ),
    workflow_path: str | None = typer.Argument(
        None, help="Path to the workflow YAML file. If omitted, uses the 'connected' workflow."
    ),
):
    """Generate boilerplate scripts for nodes in a workflow."""
    if workflow_path is None:
        workflow_path = get_current_workflow()

    if workflow_path is None:
        console.print(
            "[red]Error:[/red] No workflow specified and no active workflow set. Use [bold]langpedia use <file>[/bold] first."
        )
        raise typer.Exit(code=1)

    if not os.path.exists(workflow_path):
        console.print(f"[red]Error:[/red] Workflow file [bold]{workflow_path}[/bold] not found.")
        raise typer.Exit(code=1)

    try:
        with open(workflow_path) as f:
            data = yaml.safe_load(f)
            workflow_name = data.get("name", Path(workflow_path).stem).lower().replace(" ", "_")
            nodes = data.get("nodes", [])
    except Exception as e:
        console.print(f"[red]Error:[/red] Could not parse workflow file: {e}")
        raise typer.Exit(code=1)

    def generate_for_node(node):
        nid = node.get("id")
        ntype = node.get("type")

        if ntype == "rag_retrieve":
            target_dir = Path("scripts") / "workflows" / workflow_name / "nodes" / nid
            target_dir.mkdir(parents=True, exist_ok=True)

            scripts_content = {
                "extract.py": 'from backend.app.engine.nodes.base import NodeScript, NodeContext\n\nclass Extractor(NodeScript):\n    def run(self, ctx: NodeContext, state: dict, config: dict) -> dict:\n        """Custom extraction logic."""\n        dataset_path = state.get("dataset_path")\n        ctx.emit("extract_start", {"path": dataset_path})\n        print(f"Extracting from {dataset_path}...")\n        return {"docs": ["Doc 1", "Doc 2"]}\n',
                "vectorize.py": 'from backend.app.engine.nodes.base import NodeScript, NodeContext\n\nclass Vectorizer(NodeScript):\n    def run(self, ctx: NodeContext, state: dict, config: dict) -> dict:\n        """Custom vectorization logic."""\n        docs = state.get("docs", [])\n        ctx.emit("vectorize_docs", {"count": len(docs)})\n        print(f"Vectorizing {len(docs)} documents...")\n        return state\n',
                "store.py": 'from backend.app.engine.nodes.base import NodeScript, NodeContext\n\nclass Searcher(NodeScript):\n    def run(self, ctx: NodeContext, state: dict, config: dict) -> dict:\n        """Custom search logic."""\n        query = state.get("query")\n        top_k = state.get("top_k", 5)\n        print(f"Searching for: {query} (top_k={top_k})")\n        return {"results": [f"Result for {query}"]}\n',
            }

            mappings = {}
            for filename, content in scripts_content.items():
                file_path = target_dir / filename
                logical_name = filename.split(".")[0]
                mappings[logical_name] = str(file_path)

                if not file_path.exists():
                    with open(file_path, "w") as f:
                        f.write(content)
                    console.print(f"  [green]✔[/green] Created [bold]{file_path}[/bold]")

            console.print(f"  [green]✔[/green] Generated RAG scripts for node [bold]{nid}[/bold]")
            return mappings
        return None

    yaml_updated = False
    if node_id:
        node = next((n for n in nodes if n.get("id") == node_id), None)
        if not node:
            console.print(f"[red]Error:[/red] Node [bold]{node_id}[/bold] not found in workflow.")
            raise typer.Exit(code=1)
        mappings = generate_for_node(node)
        if mappings:
            node["scripts"] = node.get("scripts", {})
            node["scripts"].update(mappings)
            yaml_updated = True
    else:
        console.print(f"[bold cyan]Generating scripts for all nodes in workflow: {workflow_name}...[/bold cyan]")
        for node in nodes:
            mappings = generate_for_node(node)
            if mappings:
                node["scripts"] = node.get("scripts", {})
                node["scripts"].update(mappings)
                yaml_updated = True

    if yaml_updated:
        try:
            with open(workflow_path, "w") as f:
                yaml.dump(data, f, sort_keys=False)
            console.print(f"\n[green]✔[/green] [bold]{workflow_path}[/bold] updated with script paths.")
        except Exception as e:
            console.print(f"[red]Error:[/red] Could not update workflow YAML: {e}")

    if not yaml_updated:
        console.print("[yellow]No supported nodes found for script generation.[/yellow]")
    else:
        console.print("\n[bold green]Success![/bold green] Script generation complete.")


@app.command()
def run(
    file: str | None = typer.Argument(None, help="The YAML file to run. If omitted, uses the 'connected' workflow."),
    input: str = typer.Option("{}", "--input", "-i", help="JSON input for the workflow"),
    remote: str | None = typer.Option(None, "--remote", "-r", help="Remote server URL"),
    local: bool = typer.Option(True, "--local", "-l", help="Run locally (default)"),
):
    """Run a workflow. Uses the 'connected' workflow if no file is specified."""
    if file is None:
        file = get_current_workflow()

    if file is None:
        console.print(
            "[red]Error:[/red] No workflow specified and no active workflow set. Use [bold]langpedia use <file>[/bold] first."
        )
        raise typer.Exit(code=1)

    if not os.path.exists(file):
        console.print(f"[red]Error:[/red] Workflow file [bold]{file}[/bold] not found.")
        raise typer.Exit(code=1)

    input_data = json.loads(input)

    if remote:
        typer.echo(f"Running workflow {file} remotely on {remote}...")

        async def run_remote():
            async with httpx.AsyncClient() as client:
                with open(file) as f:
                    spec_data = yaml.safe_load(f)
                resp = await client.post(f"{remote}/workflows/", json=spec_data)
                workflow_id = resp.json().get("id")

                resp = await client.post(f"{remote}/runs/", params={"workflow_id": workflow_id}, json=input_data)
                typer.echo(f"Run output: {resp.json().get('outputs')}")

        asyncio.run(run_remote())
    else:
        with open(file) as f:
            spec_data = yaml.safe_load(f)

        spec = WorkflowSpec(**spec_data)

        # ─── State for the live display ───
        display_state = {
            "workflow_name": "",
            "workflow_version": "",
            "total_nodes": 0,
            "input": input_data,
            "nodes": [],          # list of node display dicts
            "current_node": None,  # index of active node
            "finished": False,
            "elapsed": 0,
            "success_count": 0,
            "fail_count": 0,
            "node_times": {},
        }

        def build_display():
            """Build the entire Rich renderable from the current state."""
            renderables = []

            # ── Header Panel ──
            header_text = Text()
            header_text.append("🚀 ", style="bold")
            header_text.append(display_state["workflow_name"], style="bold cyan")
            header_text.append(f"  v{display_state['workflow_version']}", style="dim")
            header_text.append(f"\n   Nodes: {display_state['total_nodes']}", style="white")
            input_str = json.dumps(display_state["input"])
            if len(input_str) > 50:
                input_str = input_str[:47] + "..."
            header_text.append(f"  │  Input: {input_str}", style="dim")

            renderables.append(Panel(header_text, border_style="bright_blue", padding=(0, 1)))
            renderables.append(Text(""))

            # ── Node Panels ──
            for i, node in enumerate(display_state["nodes"]):
                node_title = Text()
                status_icon = "✔" if node.get("done") else ("❌" if node.get("error") else "⏳")
                icon_style = "green" if node.get("done") else ("red" if node.get("error") else "yellow")
                node_title.append(f"  {status_icon} ", style=icon_style)
                node_title.append(f"Node {node['index']}/{display_state['total_nodes']}", style="bold white")
                node_title.append(f" ─ {node['node_id']}", style="bold cyan")

                lines = []

                # Type + description
                type_line = Text()
                type_line.append("  Type: ", style="dim")
                type_line.append(node["node_type"], style="bold magenta")
                if node.get("description"):
                    type_line.append(f" ({node['description']})", style="italic dim")
                lines.append(type_line)


                # Step progress
                if node.get("steps"):
                    lines.append(Text(""))
                    for step_name in node["steps"]:
                        step_data = node.get("step_status", {}).get(step_name, {})
                        step_state = step_data.get("state", "pending")
                        detail = step_data.get("detail", "")

                        step_line = Text()
                        if step_state == "done":
                            step_line.append("  ✔ ", style="green")
                            step_line.append(step_name, style="bold green")
                            if detail:
                                step_line.append(f" ─ {detail}", style="dim green")
                        elif step_state == "active":
                            step_line.append("  ⏳ ", style="yellow")
                            step_line.append(step_name, style="bold yellow")
                            if detail:
                                step_line.append(f" ─ {detail}", style="dim yellow")
                        else:
                            step_line.append("  ○ ", style="dim")
                            step_line.append(step_name, style="dim")
                        lines.append(step_line)

                # Elapsed time for completed nodes
                if node.get("done") and node.get("elapsed"):
                    lines.append(Text(""))
                    time_line = Text()
                    time_line.append(f"  Completed in {node['elapsed']:.2f}s", style="dim green")
                    lines.append(time_line)

                # Active spinner
                if node.get("active") and not node.get("done") and not node.get("error"):
                    lines.append(Text(""))
                    lines.append(Spinner("dots", text="  Running...", style="yellow"))

                node_panel = Panel(
                    Group(*lines),
                    title=node_title,
                    title_align="left",
                    border_style="bright_blue" if node.get("active") else ("green" if node.get("done") else "dim"),
                    padding=(0, 1),
                )
                renderables.append(node_panel)
                renderables.append(Text(""))

            # ── Footer / Summary ──
            if display_state["finished"]:
                ok = display_state["success_count"]
                fail = display_state["fail_count"]
                elapsed = display_state["elapsed"]

                footer_text = Text()
                footer_text.append("🏁 ", style="bold")
                footer_text.append("Execution Complete", style="bold green" if fail == 0 else "bold red")
                footer_text.append(f"\n   Total Time: {elapsed:.2f}s", style="white")
                footer_text.append(f"  │  Nodes: {ok} OK", style="green")
                if fail > 0:
                    footer_text.append(f" │ {fail} Failed", style="red")

                renderables.append(Panel(footer_text, border_style="green" if fail == 0 else "red", padding=(0, 1)))

            return Group(*renderables)

        def on_event(event_type: str, data: dict):
            if event_type == "workflow_start":
                display_state["workflow_name"] = data.get("name", "Workflow")
                display_state["workflow_version"] = data.get("version", "0.1")
                display_state["total_nodes"] = data.get("total_nodes", 0)

            elif event_type == "node_start":
                node_display = {
                    "node_id": data["node_id"],
                    "node_type": data.get("node_type", "unknown"),
                    "index": data.get("node_index", 0),
                    "description": data.get("description", ""),
                    "steps": [],  # Populated dynamically by __steps__ event
                    "step_status": {},
                    "active": True,
                    "done": False,
                    "error": False,
                    "elapsed": None,
                }
                display_state["nodes"].append(node_display)
                display_state["current_node"] = len(display_state["nodes"]) - 1

            elif event_type == "node_step":
                idx = display_state.get("current_node")
                if idx is not None and idx < len(display_state["nodes"]):
                    node = display_state["nodes"][idx]
                    step_name = data.get("step", "")
                    detail = data.get("detail", "")

                    # Handle __steps__ discovery event from the node
                    if step_name == "__steps__":
                        node["steps"] = [s for s in detail.split(",") if s]
                        return

                    # Add step if not yet known
                    if step_name not in node["steps"]:
                        node["steps"].append(step_name)

                    # Update step status
                    current_state = node["step_status"].get(step_name, {}).get("state", "pending")
                    if current_state == "active":
                        # Second call = done
                        node["step_status"][step_name] = {"state": "done", "detail": detail}
                    else:
                        # First call = active
                        node["step_status"][step_name] = {"state": "active", "detail": detail}

            elif event_type == "node_complete":
                idx = display_state.get("current_node")
                if idx is not None and idx < len(display_state["nodes"]):
                    node = display_state["nodes"][idx]
                    node["active"] = False
                    node["done"] = True
                    node["elapsed"] = data.get("elapsed", 0)
                    # Mark all remaining steps as done
                    for s in node["steps"]:
                        if s not in node["step_status"] or node["step_status"][s]["state"] != "done":
                            node["step_status"][s] = {"state": "done", "detail": node["step_status"].get(s, {}).get("detail", "")}
                    display_state["success_count"] += 1

            elif event_type == "node_error":
                idx = display_state.get("current_node")
                if idx is not None and idx < len(display_state["nodes"]):
                    node = display_state["nodes"][idx]
                    node["active"] = False
                    node["error"] = True
                    display_state["fail_count"] += 1

            elif event_type == "workflow_end":
                display_state["finished"] = True
                display_state["elapsed"] = data.get("elapsed", 0)

        runner = WorkflowRunner(spec, on_event=on_event)

        with Live(build_display(), console=console, refresh_per_second=8, transient=False) as live:
            async def run_with_live():
                outputs = await runner.run(input_data)
                return outputs

            import threading
            result_holder = [None]
            error_holder = [None]

            def run_in_thread():
                try:
                    result_holder[0] = asyncio.run(run_with_live())
                except Exception as e:
                    error_holder[0] = e

            t = threading.Thread(target=run_in_thread)
            t.start()

            while t.is_alive():
                live.update(build_display())
                time.sleep(0.1)
            t.join()

            # Final render
            live.update(build_display())

        if error_holder[0]:
            console.print(f"\n[red]Error during execution:[/red] {error_holder[0]}")
            raise typer.Exit(code=1)


@app.command(name="list")
def list_workflows():
    """List all workflows in the project."""
    workflow_dir = Path("workflows")
    if not workflow_dir.exists():
        console.print("[yellow]No workflows directory found. Run 'langpedia init' first.[/yellow]")
        return

    files = list(workflow_dir.glob("*.yaml"))
    current = get_current_workflow()

    table = Table(title="Available Workflows")
    table.add_column("Status", justify="center")
    table.add_column("Name")
    table.add_column("File Path", style="dim")

    for f in files:
        is_current = str(f) == current
        status = "[green]⭐[/green]" if is_current else ""
        try:
            with open(f) as wf:
                data = yaml.safe_load(wf)
                name = data.get("name", "Unnamed")
        except Exception:
            name = "[red]Invalid YAML[/red]"

        table.add_row(status, name, str(f))

    console.print(table)
    if current:
        console.print(f"\n[dim]Current active workflow:[/dim] [bold cyan]{current}[/bold cyan]")


@app.command()
def use(file: str):
    """'Connect' to a workflow to set it as the default for other commands."""
    if not os.path.exists(file):
        console.print(f"[red]Error:[/red] File [bold]{file}[/bold] does not exist.")
        raise typer.Exit(code=1)

    set_current_workflow(file)
    console.print(f"[green]✔[/green] Now using [bold cyan]{file}[/bold cyan] as the default workflow.")


@app.command()
def rag_ingest(path: str):
    """Ingest documents into the RAG system."""
    typer.echo(f"Ingesting documents from {path}...")
    # Mock for v0.1
    typer.echo("Ingestion complete (Mocked).")


@app.command()
def sync(remote: str = typer.Option("http://localhost:8000", "--remote", "-r", help="Remote server URL")):
    """Synchronize all local workflows with the Studio backend."""
    workflow_dir = Path("workflows")
    if not workflow_dir.exists():
        console.print("[yellow]No workflows directory found.[/yellow]")
        return

    files = list(workflow_dir.glob("*.yaml"))
    console.print(f"Synchronizing [bold]{len(files)}[/bold] workflows with {remote}...")

    async def do_sync():
        async with httpx.AsyncClient() as client:
            for f in files:
                try:
                    with open(f) as wf:
                        spec_data = yaml.safe_load(wf)
                    res = await client.post(f"{remote}/workflows/", json=spec_data)
                    if res.status_code == 200:
                        console.print(f"  [green]✔[/green] Synced [bold]{f.name}[/bold]")
                    else:
                        console.print(f"  [red]✘[/red] Failed to sync [bold]{f.name}[/bold]: {res.text}")
                except Exception as e:
                    console.print(f"  [red]✘[/red] Error syncing [bold]{f.name}[/bold]: {e}")

    asyncio.run(do_sync())
    console.print("\n[bold green]Synchronization complete![/bold green]")


@app.command()
def mcp_add(name: str, url: str):
    """Add an MCP server."""
    typer.echo(f"Adding MCP server {name} at {url}...")
    # Mock for v0.1
    typer.echo("MCP server added (Mocked).")


if __name__ == "__main__":
    app()
