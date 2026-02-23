from typing import Any

from pydantic import BaseModel, Field


class NodeSpec(BaseModel):
    id: str
    type: str
    inputs: list[str] = Field(default_factory=list)
    params: dict[str, Any] = Field(default_factory=dict)
    scripts: dict[str, str] = Field(default_factory=dict)  # Logical name -> file path
    parent: str | None = None


class EdgeSpec(BaseModel):
    source: str
    target: str
    sourceHandle: str | None = None
    targetHandle: str | None = None
    label: str | None = None


class WorkflowSpec(BaseModel):
    version: str = "0.1"
    name: str
    nodes: list[NodeSpec]
    edges: list[EdgeSpec] = Field(default_factory=list)
