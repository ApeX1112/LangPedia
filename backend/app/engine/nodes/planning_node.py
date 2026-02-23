from typing import Any
from .scriptable import ScriptableNode

class PlanningNode(ScriptableNode):
    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Executes planning scripts sequentially (e.g., analyze -> plan)"""
        return await self.execute_scripts_sequentially(input_data)
