from typing import Any
from .scriptable import ScriptableNode

class ThinkingNode(ScriptableNode):
    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Executes thinking scripts sequentially (e.g., reason -> conclude)"""
        return await self.execute_scripts_sequentially(input_data)
