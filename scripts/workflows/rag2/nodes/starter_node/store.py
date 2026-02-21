from backend.app.engine.nodes.base import NodeScript, NodeContext

class Searcher(NodeScript):
    def run(self, ctx: NodeContext, state: dict, config: dict) -> dict:
        """Custom search logic."""
        query = state.get("query")
        top_k = state.get("top_k", 5)
        print(f"Searching for: {query} (top_k={top_k})")
        return {"results": [f"Result for {query}"]}
