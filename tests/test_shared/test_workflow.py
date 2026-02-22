"""Tests for shared.workflow Pydantic models."""

import pytest
from pydantic import ValidationError

from shared.workflow import EdgeSpec, NodeSpec, WorkflowSpec

# ── NodeSpec ─────────────────────────────────────────────────────────────


class TestNodeSpec:
    def test_minimal_node(self):
        node = NodeSpec(id="my_node", type="llm")
        assert node.id == "my_node"
        assert node.type == "llm"
        assert node.inputs == []
        assert node.params == {}
        assert node.scripts == {}

    def test_node_with_all_fields(self):
        node = NodeSpec(
            id="rag_1",
            type="rag_retrieve",
            inputs=["input.query", "kb.docs"],
            params={"top_k": 5, "dataset_name": "wiki"},
            scripts={"extract": "scripts/extract.py"},
        )
        assert node.inputs == ["input.query", "kb.docs"]
        assert node.params["top_k"] == 5
        assert node.scripts["extract"] == "scripts/extract.py"

    def test_node_requires_id_and_type(self):
        with pytest.raises(ValidationError):
            NodeSpec()

    def test_node_requires_type(self):
        with pytest.raises(ValidationError):
            NodeSpec(id="orphan")


# ── EdgeSpec ─────────────────────────────────────────────────────────────


class TestEdgeSpec:
    def test_edge_creation(self):
        edge = EdgeSpec(source="a", target="b")
        assert edge.source == "a"
        assert edge.target == "b"

    def test_edge_requires_both_fields(self):
        with pytest.raises(ValidationError):
            EdgeSpec(source="a")


# ── WorkflowSpec ─────────────────────────────────────────────────────────


class TestWorkflowSpec:
    def test_minimal_workflow(self):
        wf = WorkflowSpec(
            name="Test",
            nodes=[NodeSpec(id="n1", type="llm")],
        )
        assert wf.name == "Test"
        assert wf.version == "0.1"
        assert len(wf.nodes) == 1
        assert wf.edges == []

    def test_workflow_with_edges(self):
        wf = WorkflowSpec(
            name="Pipeline",
            nodes=[
                NodeSpec(id="a", type="llm"),
                NodeSpec(id="b", type="llm", inputs=["a.output"]),
            ],
            edges=[EdgeSpec(source="a", target="b")],
        )
        assert len(wf.edges) == 1
        assert wf.edges[0].source == "a"

    def test_workflow_requires_name(self):
        with pytest.raises(ValidationError):
            WorkflowSpec(nodes=[NodeSpec(id="n", type="t")])

    def test_workflow_requires_nodes(self):
        with pytest.raises(ValidationError):
            WorkflowSpec(name="Empty")

    def test_workflow_serialization_roundtrip(self):
        wf = WorkflowSpec(
            name="Roundtrip",
            nodes=[NodeSpec(id="x", type="llm", params={"temp": 0.7})],
        )
        data = wf.model_dump()
        rebuilt = WorkflowSpec(**data)
        assert rebuilt.name == wf.name
        assert rebuilt.nodes[0].params["temp"] == 0.7
