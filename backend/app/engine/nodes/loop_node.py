from typing import Any
from pathlib import Path
from .scriptable import ScriptableNode
from .base import NodeContext

class LoopNode(ScriptableNode):
    def set_children(self, children: list):
        self._children = children

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Executes scripts in a loop AND runs child nodes iteratively."""
        from backend.app.engine.runner import WorkflowRunner
        from shared.workflow import WorkflowSpec

        scripts: dict[str, str] = self.spec.scripts
        if not scripts:
            scripts = self._discover_scripts()

        step_names = list(scripts.keys())
        if step_names:
            self.emit_step("__steps__", ",".join(step_names))

        ctx = NodeContext(self.id, self.run_id, self.events)
        config = self.params
        state = {**input_data}
        
        children = getattr(self, "_children", [])

        max_iterations = config.get("max_iterations", 5)
        iterations = 0

        while iterations < max_iterations:
            iterations += 1
            for step_name, script_path_str in scripts.items():
                script_path = Path(script_path_str)
                dynamic_step_name = f"{step_name}_{iterations}"
                self.emit_step(dynamic_step_name, f"Running iteration {iterations} logic...")
                
                state, log_text = await self._run_script(ctx, script_path, state, config)
                self.emit_step(dynamic_step_name, log_text or "Done")
                
            # Execute sub-DAG for this iteration
            if children:
                self.emit_step(f"sub_dag_{iterations}", f"Running container {len(children)} nodes...")
                # We create a transient mini-workflow spec for these children
                child_spec = WorkflowSpec(
                    name=f"{self.workflow_name}_loop_{self.id}_iter_{iterations}",
                    nodes=children,
                    edges=[] # We trust the runner's implicit edge resolution from inputs
                )
                
                # We pass the parent's events array to merge traces in real-time
                def _loop_event_handler(event_type, data):
                    # Passthrough sub-DAG events upstream with a prefix overlay if desired,
                    # but since they share self.events, the CLI gets them naturally.
                    if self._runner_emit:
                        # Append the iteration context to the data
                        data["loop_iter"] = iterations
                        data["loop_parent"] = self.id
                        self._runner_emit(event_type, data)

                sub_runner = WorkflowRunner(child_spec, on_event=_loop_event_handler)
                sub_outputs = await sub_runner.run(state)
                
                # Merge sub_outputs back into the state for the next iteration
                # (Optional: depends on the intended data flow)
                state[f"iteration_{iterations}_outputs"] = sub_outputs
                self.emit_step(f"sub_dag_{iterations}", "Container iteration complete.")

            # Allow the script to dynamically break the loop by modifying the state
            if state.get("loop_break", False):
                self.log(f"Loop broken at iteration {iterations}")
                break

        return state
