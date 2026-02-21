from backend.app.engine.nodes.base import NodeScript, NodeContext

class Vectorizer(NodeScript):
    def run(self, ctx: NodeContext, state: dict, config: dict) -> dict:
        """Custom vectorization logic."""
        docs = state.get("docs", [])
        ctx.emit("vectorize_docs", {"count": len(docs)})
        print(f"Vectorizing {len(docs)} documents...")
        return state
