from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol

class NodeContext:
    def __init__(self, node_id: str, run_id: str, events: List[Dict[str, Any]]):
        self.node_id = node_id
        self.run_id = run_id
        self.events = events

    def emit(self, event_type: str, payload: Dict[str, Any]):
        """Emit a structured trace event."""
        self.events.append({
            "node_id": self.node_id,
            "run_id": self.run_id,
            "type": event_type,
            "payload": payload,
            "timestamp": "..." # Set by runner or system
        })

class NodeScript(ABC):
    def validate(self, config: Dict[str, Any]) -> None:
        """Validate the configuration for this script. Raise Exception if invalid."""
        pass

    @abstractmethod
    def run(self, ctx: NodeContext, state: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Main execution logic. Returns updated state."""
        pass

    def evaluate(self, ctx: NodeContext, before: Dict[str, Any], after: Dict[str, Any], config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Optional evaluation logic after run."""
        return None

class BaseNode(ABC):
    def __init__(self, spec: Any, runner_events: List[Dict[str, Any]], workflow_name: str = "default"):
        self.spec = spec
        self.id = spec.id
        self.params = spec.params
        self.inputs = spec.inputs
        self.events = runner_events
        self.workflow_name = workflow_name
        self.run_id = "pending_run" # Should be passed from runner ideally

    def log(self, message: str, level: str = "info"):
        """Emit a log event that can be seen in terminal and UI."""
        print(f"[{self.id}] {message}")
        self.events.append({
            "node_id": self.id,
            "status": "log",
            "message": message,
            "level": level,
            "timestamp": "..."
        })

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        pass
