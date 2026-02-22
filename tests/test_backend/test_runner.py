"""Tests for the workflow execution engine."""

from backend.app.engine.runner import WorkflowRunner
from shared.workflow import EdgeSpec, NodeSpec, WorkflowSpec

# ── Basic Execution ──────────────────────────────────────────────────────


class TestWorkflowRunner:
    async def test_single_node_execution(self):
        """A single placeholder node should execute and produce output."""
        spec = WorkflowSpec(
            name="Single",
            nodes=[NodeSpec(id="only", type="placeholder", inputs=["input.query"])],
        )
        runner = WorkflowRunner(spec)
        outputs = await runner.run({"query": "hello"})

        assert "only" in outputs
        assert "input" in outputs

    async def test_two_node_chain(self, two_node_spec):
        """Nodes should execute in dependency order."""
        runner = WorkflowRunner(two_node_spec)
        outputs = await runner.run({"query": "test"})

        assert "node_a" in outputs
        assert "node_b" in outputs

    async def test_diamond_dag(self, diamond_workflow_spec):
        """Diamond dependency graph should resolve without deadlock."""
        runner = WorkflowRunner(diamond_workflow_spec)
        outputs = await runner.run({"query": "diamond"})

        assert "a" in outputs
        assert "b" in outputs
        assert "c" in outputs
        assert "d" in outputs

    async def test_initial_input_stored(self):
        """Initial input should be accessible as 'input' in node_outputs."""
        spec = WorkflowSpec(
            name="InputTest",
            nodes=[NodeSpec(id="n", type="placeholder")],
        )
        runner = WorkflowRunner(spec)
        await runner.run({"query": "hello", "context": "world"})

        assert runner.node_outputs["input"]["query"] == "hello"
        assert runner.node_outputs["input"]["context"] == "world"

    async def test_events_are_logged(self, two_node_spec):
        """Every node should produce started + completed events."""
        runner = WorkflowRunner(two_node_spec)
        await runner.run({"query": "test"})

        started = [e for e in runner.events if e["type"] == "node_start"]
        completed = [e for e in runner.events if e["type"] == "node_complete"]
        assert len(started) == 2
        assert len(completed) == 2

    async def test_event_timestamps_present(self, two_node_spec):
        """Events should include ISO timestamp strings."""
        runner = WorkflowRunner(two_node_spec)
        await runner.run({"query": "test"})

        for event in runner.events:
            assert "timestamp" in event
            assert isinstance(event["timestamp"], str)

    async def test_deadlock_detection(self):
        """Circular dependencies should NOT hang; runner should detect deadlock."""
        spec = WorkflowSpec(
            name="Deadlock",
            nodes=[
                NodeSpec(id="a", type="placeholder", inputs=["b.out"]),
                NodeSpec(id="b", type="placeholder", inputs=["a.out"]),
            ],
            edges=[
                EdgeSpec(source="a", target="b"),
                EdgeSpec(source="b", target="a"),
            ],
        )
        runner = WorkflowRunner(spec)
        outputs = await runner.run({"query": "stuck"})

        # Neither node should execute since they form a cycle
        assert "a" not in outputs
        assert "b" not in outputs

    async def test_workflow_name_derived(self):
        """Runner should derive a snake_case workflow name from the spec."""
        spec = WorkflowSpec(
            name="My Cool Workflow",
            nodes=[NodeSpec(id="n", type="placeholder")],
        )
        runner = WorkflowRunner(spec)
        assert runner.workflow_name == "my_cool_workflow"
