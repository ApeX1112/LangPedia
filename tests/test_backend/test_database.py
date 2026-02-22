"""Tests for database models and initialization."""

import uuid

from backend.app.models.database import Base, Run, Trace, Workflow


class TestDatabaseModels:
    def test_tables_created(self, db_engine):
        """init_db (via fixture) should create all three tables."""
        table_names = Base.metadata.tables.keys()
        assert "workflows" in table_names
        assert "runs" in table_names
        assert "traces" in table_names

    def test_create_workflow(self, db_session):
        wf = Workflow(
            id=str(uuid.uuid4()),
            name="Test Workflow",
            spec={"name": "Test", "nodes": [], "edges": []},
        )
        db_session.add(wf)
        db_session.commit()

        result = db_session.query(Workflow).first()
        assert result is not None
        assert result.name == "Test Workflow"
        assert result.spec["name"] == "Test"

    def test_create_run_linked_to_workflow(self, db_session):
        wf_id = str(uuid.uuid4())
        wf = Workflow(id=wf_id, name="WF", spec={})
        db_session.add(wf)
        db_session.commit()

        run = Run(id=str(uuid.uuid4()), workflow_id=wf_id, status="running")
        db_session.add(run)
        db_session.commit()

        result = db_session.query(Run).first()
        assert result.workflow_id == wf_id
        assert result.status == "running"

    def test_create_trace_with_events(self, db_session):
        wf_id = str(uuid.uuid4())
        run_id = str(uuid.uuid4())
        db_session.add(Workflow(id=wf_id, name="WF", spec={}))
        db_session.add(Run(id=run_id, workflow_id=wf_id, status="completed"))
        db_session.commit()

        events = [
            {"node_id": "n1", "status": "started"},
            {"node_id": "n1", "status": "completed"},
        ]
        trace = Trace(id=str(uuid.uuid4()), run_id=run_id, events=events)
        db_session.add(trace)
        db_session.commit()

        result = db_session.query(Trace).first()
        assert result.run_id == run_id
        assert len(result.events) == 2

    def test_workflow_created_at_auto_set(self, db_session):
        wf = Workflow(id=str(uuid.uuid4()), name="Timestamped", spec={})
        db_session.add(wf)
        db_session.commit()

        result = db_session.query(Workflow).first()
        assert result.created_at is not None
