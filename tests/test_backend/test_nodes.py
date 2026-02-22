"""Tests for base node classes and the node registry."""

from backend.app.engine.nodes.base import BaseNode, NodeContext, NodeScript
from backend.app.engine.nodes.registry import NODE_REGISTRY
from shared.workflow import NodeSpec

# ── NodeContext ──────────────────────────────────────────────────────────


class TestNodeContext:
    def test_emit_appends_event(self):
        events = []
        ctx = NodeContext(node_id="test_node", run_id="run_123", events=events)
        ctx.emit("custom_event", {"key": "value"})

        assert len(events) == 1
        assert events[0]["node_id"] == "test_node"
        assert events[0]["run_id"] == "run_123"
        assert events[0]["type"] == "custom_event"
        assert events[0]["payload"]["key"] == "value"

    def test_emit_multiple_events(self):
        events = []
        ctx = NodeContext(node_id="n", run_id="r", events=events)
        ctx.emit("start", {})
        ctx.emit("end", {})
        assert len(events) == 2


# ── NodeScript ───────────────────────────────────────────────────────────


class TestNodeScript:
    def test_concrete_script_can_run(self):
        class MyScript(NodeScript):
            def run(self, ctx, state, config):
                state["processed"] = True
                return state

        script = MyScript()
        events = []
        ctx = NodeContext("n", "r", events)
        result = script.run(ctx, {"raw": True}, {})
        assert result["processed"] is True

    def test_validate_is_noop_by_default(self):
        class Minimal(NodeScript):
            def run(self, ctx, state, config):
                return state

        script = Minimal()
        # Should not raise
        script.validate({"any": "config"})

    def test_evaluate_returns_none_by_default(self):
        class Minimal(NodeScript):
            def run(self, ctx, state, config):
                return state

        script = Minimal()
        events = []
        ctx = NodeContext("n", "r", events)
        result = script.evaluate(ctx, {}, {}, {})
        assert result is None


# ── BaseNode ─────────────────────────────────────────────────────────────


class TestBaseNode:
    def test_log_appends_event(self):
        spec = NodeSpec(id="my_node", type="placeholder")
        events = []
        node = _make_concrete_node(spec, events)
        node.log("Hello world")

        assert len(events) == 1
        assert events[0]["node_id"] == "my_node"
        assert events[0]["status"] == "log"
        assert events[0]["message"] == "Hello world"

    def test_log_with_level(self):
        spec = NodeSpec(id="n", type="t")
        events = []
        node = _make_concrete_node(spec, events)
        node.log("error occurred", level="error")
        assert events[0]["level"] == "error"

    def test_node_properties_from_spec(self):
        spec = NodeSpec(
            id="rag_1",
            type="rag_retrieve",
            inputs=["input.query"],
            params={"top_k": 3},
        )
        node = _make_concrete_node(spec, [])
        assert node.id == "rag_1"
        assert node.params["top_k"] == 3
        assert node.inputs == ["input.query"]


# ── Registry ─────────────────────────────────────────────────────────────


class TestNodeRegistry:
    def test_rag_retrieve_registered(self):
        assert "rag_retrieve" in NODE_REGISTRY

    def test_registry_values_are_basenode_subclasses(self):
        for name, cls in NODE_REGISTRY.items():
            assert issubclass(cls, BaseNode), f"{name} is not a BaseNode subclass"


# ── Helpers ──────────────────────────────────────────────────────────────


def _make_concrete_node(spec, events):
    """Create a concrete BaseNode subclass for testing."""

    class ConcreteNode(BaseNode):
        async def execute(self, input_data):
            return {"ok": True}

    return ConcreteNode(spec, events)
