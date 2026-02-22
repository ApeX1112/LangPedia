"""Tests for the FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient

from backend.app.api.main import app
from backend.app.models.database import init_db


@pytest.fixture(autouse=True)
def _setup_db():
    """Ensure database tables exist before API tests run."""
    init_db()


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


class TestRootEndpoint:
    def test_root_returns_welcome(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Langpedia" in data["message"]


class TestWorkflowEndpoints:
    def test_create_workflow(self, client):
        payload = {
            "name": "Test Workflow",
            "nodes": [{"id": "n1", "type": "llm"}],
        }
        response = client.post("/workflows/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["status"] == "created"

    def test_list_workflows_returns_list(self, client):
        response = client.get("/workflows/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_nonexistent_workflow(self, client):
        response = client.get("/workflows/nonexistent-id")
        assert response.status_code == 200
        data = response.json()
        assert "error" in data

    def test_create_then_list_contains_workflow(self, client):
        payload = {
            "name": "Listed WF",
            "nodes": [{"id": "n1", "type": "placeholder"}],
        }
        client.post("/workflows/", json=payload)
        response = client.get("/workflows/")
        names = [w["name"] for w in response.json()]
        # DB-sourced workflows don't have "(Local)" suffix
        assert any("Listed WF" in name for name in names)
