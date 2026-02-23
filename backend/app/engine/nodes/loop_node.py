from typing import Any
from pathlib import Path
from .scriptable import ScriptableNode
from .base import NodeContext

class LoopNode(ScriptableNode):
    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Executes scripts in a loop until max_iterations is reached or loop_break is True in state."""
        scripts: dict[str, str] = self.spec.scripts
        if not scripts:
            scripts = self._discover_scripts()

        step_names = list(scripts.keys())
        if step_names:
            self.emit_step("__steps__", ",".join(step_names))

        ctx = NodeContext(self.id, self.run_id, self.events)
        config = self.params
        state = {**input_data}

        max_iterations = config.get("max_iterations", 5)
        iterations = 0

        while iterations < max_iterations:
            iterations += 1
            for step_name, script_path_str in scripts.items():
                script_path = Path(script_path_str)
                dynamic_step_name = f"{step_name}_{iterations}"
                self.emit_step(dynamic_step_name, f"Running iteration {iterations}...")
                
                state, log_text = await self._run_script(ctx, script_path, state, config)
                self.emit_step(dynamic_step_name, log_text or "Done")
            
            # Allow the script to dynamically break the loop by modifying the state
            if state.get("loop_break", False):
                self.log(f"Loop broken at iteration {iterations}")
                break

        return state
