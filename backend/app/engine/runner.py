import asyncio
from typing import Dict, Any, List
from shared.workflow import WorkflowSpec, NodeSpec

class WorkflowRunner:
    def __init__(self, spec: WorkflowSpec):
        self.spec = spec
        self.node_outputs: Dict[str, Any] = {}
        self.events: List[Dict[str, Any]] = []

    async def run(self, initial_input: Dict[str, Any]):
        self.node_outputs["input"] = initial_input
        
        # Simple execution: topological sort or just sequential for MVP if graph is linear
        # For a true graph, we'd need a proper scheduler.
        # Let's assume a DAG and use a simple dependency-based execution.
        
        executed_nodes = set()
        to_execute = list(self.spec.nodes)
        
        while to_execute:
            for node in list(to_execute):
                # Check if all inputs are ready
                # Inputs are in format "node_id.field"
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
        
        return self.node_outputs

    async def execute_node(self, node: NodeSpec):
        print(f"Executing node: {node.id} ({node.type})")
        # Emit 'started' event
        self.events.append({"node_id": node.id, "status": "started", "timestamp": "..."})
        
        # Mock execution logic for v0.1
        await asyncio.sleep(0.1) 
        
        output = {"status": "success", "result": f"Output from {node.id}"}
        
        if node.type == "llm":
            output = {"text": f"LLM responded to {node.params.get('prompt', '')}"}
        elif node.type == "rag_retrieve":
            output = {"docs": ["Doc 1", "Doc 2"]}
            
        self.node_outputs[node.id] = output
        
        # Emit 'completed' event
        self.events.append({
            "node_id": node.id, 
            "status": "completed", 
            "payload": {"output": output},
            "timestamp": "..."
        })
