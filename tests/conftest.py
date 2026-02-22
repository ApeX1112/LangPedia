"""Shared test fixtures for LangPedia test suite."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.models.database import Base
from shared.workflow import EdgeSpec, NodeSpec, WorkflowSpec

# ── Sample workflow specs ────────────────────────────────────────────────


@pytest.fixture
def simple_node_spec():
    """A single node with no dependencies."""
    return NodeSpec(id="node_a", type="placeholder", params={"key": "value"})


@pytest.fixture
def two_node_spec():
    """Two connected nodes: node_a -> node_b."""
    return WorkflowSpec(
        name="Two Node Workflow",
        nodes=[
            NodeSpec(id="node_a", type="placeholder", inputs=["input.query"]),
            NodeSpec(id="node_b", type="placeholder", inputs=["node_a.result"]),
        ],
        edges=[EdgeSpec(source="node_a", target="node_b")],
    )


@pytest.fixture
def diamond_workflow_spec():
    """Diamond DAG: A -> B, A -> C, B -> D, C -> D."""
    return WorkflowSpec(
        name="Diamond Workflow",
        nodes=[
            NodeSpec(id="a", type="placeholder", inputs=["input.query"]),
            NodeSpec(id="b", type="placeholder", inputs=["a.result"]),
            NodeSpec(id="c", type="placeholder", inputs=["a.result"]),
            NodeSpec(id="d", type="placeholder", inputs=["b.result", "c.result"]),
        ],
        edges=[
            EdgeSpec(source="a", target="b"),
            EdgeSpec(source="a", target="c"),
            EdgeSpec(source="b", target="d"),
            EdgeSpec(source="c", target="d"),
        ],
    )


# ── Database fixtures ────────────────────────────────────────────────────


@pytest.fixture
def db_engine():
    """In-memory SQLite engine for tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """Database session scoped to a single test."""
    session_factory = sessionmaker(bind=db_engine)
    session = session_factory()
    yield session
    session.rollback()
    session.close()


# ── Temp directories ─────────────────────────────────────────────────────


@pytest.fixture
def tmp_workflows_dir(tmp_path):
    """Temporary directory for workflow YAML files."""
    workflows = tmp_path / "workflows"
    workflows.mkdir()
    return workflows
