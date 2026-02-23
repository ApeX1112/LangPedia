import asyncio
import time
from collections.abc import Callable
from datetime import datetime
from typing import Any

from shared.workflow import NodeSpec, WorkflowSpec

from .nodes.registry import NODE_INFO, NODE_REGISTRY


class WorkflowRunner:
    def __init__(self, spec: WorkflowSpec, on_event: Callable | None = None):
        self.spec = spec
        self.node_outputs: dict[str, Any] = {}
        self.events: list[dict[str, Any]] = []
        self.workflow_name = spec.name.lower().replace(" ", "_")
        self.on_event = on_event or self._default_event_handler

    def _default_event_handler(self, event_type: str, data: dict[str, Any]):
        """Fallback handler when no CLI callback is provided."""
        if event_type == "workflow_start":
            print(f"\n🚀 Starting Workflow Execution: {data['name']}")
        elif event_type == "node_start":
            print(f"--- Executing: {data['node_id']} ---")
        elif event_type == "node_log":
            print(f"[{data['node_id']}] {data['message']}")
        elif event_type == "node_step":
            print(f"  → {data['step']}: {data.get('detail', '')}")
        elif event_type == "node_complete":
            elapsed = data.get("elapsed", 0)
            print(f"--- Completed: {data['node_id']} ({elapsed:.2f}s) ---")
        elif event_type == "node_error":
            print(f"❌ Error in {data['node_id']}: {data['error']}")
        elif event_type == "workflow_end":
            print(f"🏁 Workflow Finished: {data['name']} ({data['elapsed']:.2f}s)\n")

    def emit(self, event_type: str, data: dict[str, Any]):
        """Emit an event to the callback and store it."""
        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            **data,
        }
        self.events.append(event)
        self.on_event(event_type, data)

    def log_event(self, node_id: str, status: str, payload: dict[str, Any] = None):
        """Legacy log_event for backward compatibility with BaseNode.log()."""
        if status == "log":
            self.emit("node_log", {"node_id": node_id, "message": payload.get("message", ""), **(payload or {})})

    async def run(self, initial_input: dict[str, Any]):
        self.node_outputs["input"] = initial_input
        total_nodes = len(self.spec.nodes)
        wf_start = time.time()

        self.emit(
            "workflow_start",
            {
                "name": self.spec.name,
                "version": self.spec.version,
                "total_nodes": total_nodes,
                "input": initial_input,
            },
        )

        executed_nodes = set()
        skipped_nodes = set()
        
        # Only execute top-level nodes initially (nodes without a parent)
        to_execute = [n for n in self.spec.nodes if not n.parent]
        node_index = 0

        while to_execute:
            made_progress = False
            for node in list(to_execute):
                can_run = True
                should_skip = False
                
                # Check dependencies
                for input_ref in node.inputs:
                    parts = input_ref.split(".")
                    source_node_id = parts[0]
                    field = parts[1] if len(parts) > 1 else None
                    
                    if source_node_id in skipped_nodes:
                        # If our dependency was skipped, we must skip too
                        should_skip = True
                        break
                        
                    if source_node_id not in self.node_outputs and source_node_id != "input":
                        can_run = False
                        break
                        
                    if source_node_id in self.node_outputs:
                        # Check explicit branch conditions inside inputs e.g., `condition_node.true`
                        # If the output explicitly emitted a `branch` and we requested a specifically mismatched field, skip it.
                        out = self.node_outputs[source_node_id]
                        if isinstance(out, dict) and "branch" in out and field is not None:
                            if out["branch"] != field:
                                should_skip = True
                                break
                        
                if should_skip:
                    # Also cascade skip to children if we skipped a container
                    nodes_to_skip = [node.id]
                    for spec_node in self.spec.nodes:
                        if spec_node.parent == node.id:
                            nodes_to_skip.append(spec_node.id)
                            
                    for skip_id in nodes_to_skip:
                        skipped_nodes.add(skip_id)
                        if any(n.id == skip_id for n in to_execute):
                            to_execute = [n for n in to_execute if n.id != skip_id]
                            self.emit("node_log", {
                                "node_id": skip_id, 
                                "message": f"Skipped due to unfulfilled branch condition."
                            })
                            
                    made_progress = True
                    continue

                if can_run:
                    node_index += 1
                    node_info = NODE_INFO.get(node.type, {})
                    self.emit(
                        "node_start",
                        {
                            "node_id": node.id,
                            "node_type": node.type,
                            "node_index": node_index,
                            "total_nodes": total_nodes,
                            "description": node_info.get("description", node.type),
                        },
                    )

                    node_start = time.time()
                    
                    # If this is a loop node, we need to pass its children down to it
                    if node.type == "loop":
                        child_nodes = [n for n in self.spec.nodes if n.parent == node.id]
                        await self.execute_node(node, child_nodes=child_nodes)
                    else:
                        await self.execute_node(node)
                        
                    elapsed = time.time() - node_start

                    output = self.node_outputs.get(node.id, {})
                    has_error = "error" in output
                    
                    # Branch Skipping Logic based on Edge Spec
                    branch = output.get("branch") if isinstance(output, dict) else None
                    if branch is not None:
                        # Find all edges originating from this node
                        out_edges = [e for e in self.spec.edges if e.source == node.id]
                        for edge in out_edges:
                            # If an edge explicitly requires a branch (`sourceHandle`), and we didn't output it
                            if edge.sourceHandle and edge.sourceHandle != branch:
                                # Mark the downstream target node as skipped
                                nodes_to_skip = [edge.target]
                                
                                # Cascade skip down to any child nodes (e.g., inside a skipped loop)
                                for spec_node in self.spec.nodes:
                                    if spec_node.parent == edge.target:
                                        nodes_to_skip.append(spec_node.id)
                                        
                                for skip_id in nodes_to_skip:
                                    skipped_nodes.add(skip_id)
                                    # Immediately remove the skipped node from the execution queue if it's there
                                    to_execute = [n for n in to_execute if n.id != skip_id]
                                    self.emit("node_log", {
                                        "node_id": skip_id, 
                                        "message": f"Preemptively skipped because '{node.id}' branched to '{branch}' instead of '{edge.sourceHandle}'."
                                    })

                    if has_error:
                        self.emit("node_error", {"node_id": node.id, "error": str(output.get("error"))})
                    else:
                        self.emit(
                            "node_complete",
                            {
                                "node_id": node.id,
                                "elapsed": elapsed,
                                "output_keys": list(output.keys()) if isinstance(output, dict) else [],
                            },
                        )

                    executed_nodes.add(node.id)
                    if node in to_execute:
                        to_execute.remove(node)
                    made_progress = True

            if not made_progress and to_execute:
                self.emit(
                    "node_error", {"node_id": "deadlock", "error": f"Cannot execute: {[n.id for n in to_execute]}"}
                )
                break
                
        wf_elapsed = time.time() - wf_start
        self.emit(
            "workflow_end",
            {
                "name": self.spec.name,
                "elapsed": wf_elapsed,
                "total_executed": len(executed_nodes),
                "total_skipped": len(skipped_nodes),
                "total_nodes": total_nodes,
            },
        )
        return self.node_outputs

    async def execute_node(self, node: NodeSpec, child_nodes: list[NodeSpec] = None):
        # Prepare inputs for the node
        input_data = {}
        for input_ref in node.inputs:
            parts = input_ref.split(".")
            source_id = parts[0]
            field = parts[1] if len(parts) > 1 else None

            source_output = self.node_outputs.get(source_id, {})
            
            # CONDITION CHECK LOGIC:
            # If the user required `condition_node.true` but condition output `branch` is `false`,
            # we should technically halt, but the runner loops handled skip logic above.
            # To be robust, if the node requests a specific branch and the state says otherwise,
            # we could raise an error, but for simplicity we'll just pass the data.
            
            if field:
                input_data[field] = source_output.get(field)
            else:
                input_data.update(source_output if isinstance(source_output, dict) else {"data": source_output})

        try:
            if node.type in NODE_REGISTRY:
                node_instance = NODE_REGISTRY[node.type](node, self.events, self.workflow_name)
                # Inject the runner's emit function so nodes can emit step events
                node_instance._runner_emit = self.emit
                
                # Inject child nodes if requested (for loop container)
                if child_nodes is not None and hasattr(node_instance, "set_children"):
                    node_instance.set_children(child_nodes)
                    
                output = await node_instance.execute(input_data)
            else:
                self.emit(
                    "node_log",
                    {"node_id": node.id, "message": f"No implementation for '{node.type}', using placeholder."},
                )
                await asyncio.sleep(0.5)
                output = {"status": "success", "message": f"Placeholder output for {node.id}"}
        except Exception as e:
            output = {"error": str(e)}

        self.node_outputs[node.id] = output
