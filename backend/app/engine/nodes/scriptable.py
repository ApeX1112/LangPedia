import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Any

from .base import BaseNode, NodeContext, NodeScript


class ScriptableNode(BaseNode):
    def _discover_scripts(self) -> dict[str, str]:
        """Fallback: discover scripts from organized path."""
        organized = Path("scripts") / "workflows" / self.workflow_name / "nodes" / self.id
        scripts = {}
        if organized.exists():
            for f in sorted(organized.glob("*.py")):
                scripts[f.stem] = str(f)
        return scripts

    async def _run_script(
        self, ctx: NodeContext, script_path: Path, state: dict[str, Any], config: dict[str, Any]
    ) -> tuple[dict[str, Any], str]:
        """Load and run a NodeScript. Returns (updated_state, log_text)."""
        if not script_path.exists():
            return state, f"Not found: {script_path}"

        try:
            module_name = f"_lp_{script_path.stem}_{id(self)}"
            spec = importlib.util.spec_from_file_location(module_name, str(script_path))
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            script_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if inspect.isclass(attr) and issubclass(attr, NodeScript) and attr is not NodeScript:
                    script_class = attr
                    break

            if not script_class:
                return state, "No NodeScript class found"

            instance = script_class()
            instance.validate(config)

            before_state = state.copy()
            after_state = instance.run(ctx, state, config)
            if after_state is None:
                after_state = state

            log_text = instance.log()

            eval_res = instance.evaluate(ctx, before_state, after_state, config)
            if eval_res:
                self.log(f"Evaluation: {eval_res}")

            del sys.modules[module_name]

            return after_state, log_text

        except Exception as e:
            self.log(f"Error in {script_path.name}: {str(e)}", level="error")
            return state, f"Error: {str(e)}"

    async def execute_scripts_sequentially(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Standard sequence logic for most scriptable nodes."""
        scripts: dict[str, str] = self.spec.scripts
        if not scripts:
            scripts = self._discover_scripts()

        step_names = list(scripts.keys())
        if step_names:
            self.emit_step("__steps__", ",".join(step_names))

        ctx = NodeContext(self.id, self.run_id, self.events)
        config = self.params
        state = {**input_data}

        for step_name, script_path_str in scripts.items():
            script_path = Path(script_path_str)
            self.emit_step(step_name, "Running...")

            state, log_text = await self._run_script(ctx, script_path, state, config)

            self.emit_step(step_name, log_text or "Done")

        return state
