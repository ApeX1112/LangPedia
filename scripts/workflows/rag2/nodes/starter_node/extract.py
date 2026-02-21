from backend.app.engine.nodes.base import NodeScript, NodeContext

class Extractor(NodeScript):
    def run(self, ctx: NodeContext, state: dict, config: dict) -> dict:
        """Custom extraction logic."""
        dataset_path = state.get("dataset_path")
        ctx.emit("extract_start", {"path": dataset_path})
        print(f"Extracting from {dataset_path}...")
        return {"docs": ["Doc 1", "Doc 2"]}
