from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class NodeSpec(BaseModel):
    id: str
    type: str
    inputs: List[str] = Field(default_factory=list)
    params: Dict[str, Any] = Field(default_factory=dict)

class EdgeSpec(BaseModel):
    source: str
    target: str

class WorkflowSpec(BaseModel):
    version: str = "0.1"
    name: str
    nodes: List[NodeSpec]
    edges: List[EdgeSpec] = Field(default_factory=list)
