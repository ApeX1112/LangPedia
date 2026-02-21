import os
import importlib.util
import sys
import inspect
from typing import Any, Dict, List
from .base import BaseNode, NodeContext, NodeScript
from pathlib import Path

class RAGRetrieveNode(BaseNode):
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        dataset_name = self.params.get("dataset_name")
        query = self.params.get("query", input_data.get("query", ""))
        top_k = self.params.get("top_k", 5)

        # Organized scripts path: scripts/workflows/<workflow_name>/nodes/<node_id>/
        organized_scripts_path = Path("scripts") / "workflows" / self.workflow_name / "nodes" / self.id
        
        # Fallback path: data/<dataset_name>/scripts/
        fallback_scripts_path = Path("data") / dataset_name / "scripts" if dataset_name else None

        self.log(f"Starting RAG retrieval (Workflow: {self.workflow_name}, Node: {self.id})")

        # Helper to find script
        def get_script_path(script_name):
            # 1. Check YAML scripts field mapping
            logical_name = script_name.split(".")[0]
            if logical_name in self.spec.scripts:
                yml_path = Path(self.spec.scripts[logical_name])
                if yml_path.exists():
                    return yml_path
                self.log(f"Script mapping {logical_name} -> {yml_path} not found", level="warning")

            # 2. Check Organized Path
            if (organized_scripts_path / script_name).exists():
                return organized_scripts_path / script_name
            
            # 3. Check Fallback Path
            if fallback_scripts_path and (fallback_scripts_path / script_name).exists():
                return fallback_scripts_path / script_name
            return None

        # Context for scripts
        ctx = NodeContext(self.id, self.run_id, self.events)
        config = self.params # Use node params as script config

        # 1. Extraction
        extract_script = get_script_path("extract.py")
        if extract_script:
            self.log(f"Running extraction script: {extract_script}")
            state = {"dataset_path": str(Path("data") / dataset_name) if dataset_name else None}
            res_state = await self.run_script(ctx, extract_script, state, config)
            docs = res_state.get("docs", [])
        else:
            self.log("Using default extraction")
            docs = [f"Default doc from {dataset_name}"]
        
        if docs is None: docs = []
        self.log(f"Extracted {len(docs)} documents")

        # 2. Vectorization
        vectorize_script = get_script_path("vectorize.py")
        if vectorize_script:
            self.log(f"Running vectorization script: {vectorize_script}")
            await self.run_script(ctx, vectorize_script, {"docs": docs}, config)
        else:
            self.log("Skipping vectorization (no script found)")

        # 3. Retrieval
        store_script = get_script_path("store.py")
        if store_script:
            self.log(f"Running retrieval script: {store_script}")
            res_state = await self.run_script(ctx, store_script, {"query": query, "top_k": top_k}, config)
            results = res_state.get("results", [])
        else:
            self.log("Using mock retrieval results")
            results = docs[:top_k]

        if results is None: results = []
        self.log(f"Retrieved {len(results)} results")
        
        return {
            "results": results,
            "dataset": dataset_name,
            "query": query
        }

    async def run_script(self, ctx: NodeContext, script_path: Path, state: Dict[str, Any], config: Dict[str, Any]):
        """Dynamically load and run a NodeScript class from a python file."""
        if not script_path.exists():
            return state

        try:
            module_name = script_path.stem
            spec = importlib.util.spec_from_file_location(module_name, str(script_path))
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Find a class that inherits from NodeScript
            script_class = None
            from .base import NodeScript # Ensure base class is available for comparison
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if inspect.isclass(attr) and issubclass(attr, NodeScript) and attr is not NodeScript:
                    script_class = attr
                    break
            
            if not script_class:
                self.log(f"No NodeScript class found in {script_path.name}", level="error")
                return state

            # lifecycle: instantiate -> validate -> run -> evaluate
            instance = script_class()
            instance.validate(config)
            
            before_state = state.copy()
            after_state = instance.run(ctx, state, config)
            if after_state is None: after_state = state # Handle missing return
            
            eval_res = instance.evaluate(ctx, before_state, after_state, config)
            if eval_res:
                self.log(f"Script evaluation result: {eval_res}")
                
            return after_state

        except Exception as e:
            self.log(f"Error running {script_path.name}: {str(e)}", level="error")
            import traceback
            print(traceback.format_exc())
            return state
