from .advanced_rag_node import AdvancedRAGNode
from .base import BaseNode
from .condition_node import ConditionNode
from .loop_node import LoopNode
from .planning_node import PlanningNode
from .rag_node import RAGRetrieveNode
from .thinking_node import ThinkingNode

NODE_REGISTRY: dict[str, type[BaseNode]] = {
    "rag_retrieve": RAGRetrieveNode,
    "planning": PlanningNode,
    "thinking": ThinkingNode,
    "advanced_rag": AdvancedRAGNode,
    "condition": ConditionNode,
    "loop": LoopNode,
}

# Metadata for beautiful CLI display
NODE_INFO: dict[str, dict] = {
    "rag_retrieve": {
        "description": "Retrieval-Augmented Generation",
    },
    "planning": {
        "description": "Orchestrates planning tasks",
    },
    "thinking": {
        "description": "Encapsulates reasoning and thought generation",
    },
    "advanced_rag": {
        "description": "RAG with self-reflection and multi-agent retrieval support",
    },
    "condition": {
        "description": "Evaluates conditions to control workflow paths",
    },
    "loop": {
        "description": "Executes logic iteratively until a terminal condition is met",
    },
}
