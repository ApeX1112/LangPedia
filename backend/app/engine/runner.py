import asyncio
from datetime import datetime
from typing import Any

from shared.workflow import NodeSpec, WorkflowSpec

from .nodes.registry import NODE_REGISTRY


class WorkflowRunner:
    def __init__(self, spec: WorkflowSpec):
        self.spec = spec
        self.node_outputs: dict[str, Any] = {}
        self.events: list[dict[str, Any]] = []
        # Try to derive a clean name from the workflow spec
        self.workflow_name = spec.name.lower().replace(" ", "_")

    def log_event(self, node_id: str, status: str, payload: dict[str, Any] = None):
        event = {
            "node_id": node_id,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "payload": payload or {},
        }
        self.events.append(event)

        # Immediate terminal output for "live" feel
        if status == "started":
            print(f"--- Executing: {node_id} ---")
        elif status == "completed":
            print(f"--- Completed: {node_id} ---")
        elif status == "log":
            # Logs from within the node are handled by the node's log() method calling this indirectly
            pass

    async def run(self, initial_input: dict[str, Any]):
        self.node_outputs["input"] = initial_input
        print(f"\n🚀 Starting Workflow Execution: {self.spec.name}")

        executed_nodes = set()
        to_execute = list(self.spec.nodes)

        while to_execute:
            made_progress = False
            for node in list(to_execute):
                can_run = True
                for input_ref in node.inputs:
                    source_node_id = input_ref.split(".")[0]
                    if source_node_id not in self.node_outputs and source_node_id != "input":
                        can_run = False
                        break

                if can_run:
                    await self.execute_node(node)
                    executed_nodes.add(node.id)
                    to_execute.remove(node)
                    made_progress = True

            if not made_progress and to_execute:
                print(f"❌ Deadlock detected: Cannot execute remaining nodes: {[n.id for n in to_execute]}")
                break

        print(f"🏁 Workflow Finished: {self.spec.name}\n")
        return self.node_outputs

    async def execute_node(self, node: NodeSpec):
        self.log_event(node.id, "started")

        # Prepare inputs for the node
        input_data = {}
        for input_ref in node.inputs:
            parts = input_ref.split(".")
            source_id = parts[0]
            field = parts[1] if len(parts) > 1 else None

            source_output = self.node_outputs.get(source_id, {})
            if field:
                input_data[field] = source_output.get(field)
            else:
                # Merge if no field specified (or just provide whole output)
                input_data.update(source_output if isinstance(source_output, dict) else {"data": source_output})

        try:
            if node.type in NODE_REGISTRY:
                node_instance = NODE_REGISTRY[node.type](node, self.events, self.workflow_name)
                output = await node_instance.execute(input_data)
            else:
                # Fallback for generic/placeholder nodes
                print(f"Warning: No implementation for node type '{node.type}', using placeholder.")
                await asyncio.sleep(0.5)
                output = {"status": "success", "message": f"Placeholder output for {node.id}"}
        except Exception as e:
            print(f"Error executing node {node.id}: {e}")
            output = {"error": str(e)}
            self.log_event(node.id, "failed", {"error": str(e)})

        self.node_outputs[node.id] = output
        self.log_event(node.id, "completed", {"output": output})
