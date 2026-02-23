from typing import Any

from .scriptable import ScriptableNode


class ConditionNode(ScriptableNode):
    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Executes condition evaluation scripts and populates the state with decisions."""
        return await self.execute_scripts_sequentially(input_data)
