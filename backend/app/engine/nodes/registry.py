from .base import BaseNode
from .rag_node import RAGRetrieveNode

NODE_REGISTRY: dict[str, type[BaseNode]] = {
    "rag_retrieve": RAGRetrieveNode,
    # Add other node types here as they are implemented
}

# Metadata for beautiful CLI display
NODE_INFO: dict[str, dict] = {
    "rag_retrieve": {
        "description": "Retrieval-Augmented Generation",
    },
}
