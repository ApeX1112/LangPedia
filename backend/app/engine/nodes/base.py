from abc import ABC, abstractmethod
from typing import Any


class NodeContext:
    def __init__(self, node_id: str, run_id: str, events: list[dict[str, Any]]):
        self.node_id = node_id
        self.run_id = run_id
        self.events = events

    def emit(self, event_type: str, payload: dict[str, Any]):
        """Emit a structured trace event."""
        self.events.append(
            {
                "node_id": self.node_id,
                "run_id": self.run_id,
                "type": event_type,
                "payload": payload,
                "timestamp": "...",  # Set by runner or system
            }
        )


class NodeScript(ABC):
    def validate(self, config: dict[str, Any]) -> None:
        """Validate the configuration for this script. Raise Exception if invalid."""
        pass

    @abstractmethod
    def run(self, ctx: NodeContext, state: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        """Main execution logic. Returns updated state."""
        pass

    def evaluate(
        self, ctx: NodeContext, before: dict[str, Any], after: dict[str, Any], config: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Optional evaluation logic after run."""
        return None


class BaseNode(ABC):
    def __init__(self, spec: Any, runner_events: list[dict[str, Any]], workflow_name: str = "default"):
        self.spec = spec
        self.id = spec.id
        self.params = spec.params
        self.inputs = spec.inputs
        self.events = runner_events
        self.workflow_name = workflow_name
        self.run_id = "pending_run"  # Should be passed from runner ideally

    def log(self, message: str, level: str = "info"):
        """Emit a log event that can be seen in terminal and UI."""
        print(f"[{self.id}] {message}")
        self.events.append(
            {"node_id": self.id, "status": "log", "message": message, "level": level, "timestamp": "..."}
        )

    @abstractmethod
    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        pass
