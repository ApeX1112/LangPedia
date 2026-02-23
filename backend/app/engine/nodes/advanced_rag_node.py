from pathlib import Path
from typing import Any

from .base import NodeContext
from .scriptable import ScriptableNode


class AdvancedRAGNode(ScriptableNode):
    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Advanced RAG logic providing a framework for self-reflective and agentic retrieval patterns."""
        scripts: dict[str, str] = self.spec.scripts
        if not scripts:
            scripts = self._discover_scripts()

        step_names = list(scripts.keys())
        if step_names:
            self.emit_step("__steps__", ",".join(step_names))

        ctx = NodeContext(self.id, self.run_id, self.events)
        config = self.params
        state = {**input_data}

        max_reflections = config.get("max_reflections", 3)
        reflection_count = 0

        for step_name, script_path_str in scripts.items():
            script_path = Path(script_path_str)

            if step_name == "reflect":
                # Special handler for 'reflect' step supporting self-reflection RAG / CRAG
                while reflection_count < max_reflections:
                    self.emit_step(step_name, "Reflecting...")
                    state, log_text = await self._run_script(ctx, script_path, state, config)

                    if state.get("reflection_passed", True):
                        self.emit_step(step_name, log_text or "Passed reflection")
                        break

                    reflection_count += 1
                    self.emit_step(step_name, f"Reflecting ({reflection_count}/{max_reflections})...")
            else:
                self.emit_step(step_name, "Running...")
                state, log_text = await self._run_script(ctx, script_path, state, config)
                self.emit_step(step_name, log_text or "Done")

        return state
