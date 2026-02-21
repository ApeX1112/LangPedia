from typing import Dict, Type
from .base import BaseNode
from .rag_node import RAGRetrieveNode

NODE_REGISTRY: Dict[str, Type[BaseNode]] = {
    "rag_retrieve": RAGRetrieveNode,
    # Add other node types here as they are implemented
}
