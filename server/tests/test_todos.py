"""Visible tests for the Python Todo API starter.

Run with: pytest server/tests -v
These are the tests candidates can see while working.
"""

import pytest


class TestBasicCrud:
    async def test_get_empty_list(self, client):
        """GET /api/todos should return an empty list initially."""
        res = await client.get("/api/todos")
        assert res.status_code == 200
        assert res.json()["todos"] == []

    async def test_post_creates_todo(self, client):
        """POST /api/todos should create a new todo."""
        res = await client.post("/api/todos", json={"title": "Buy groceries"})
        assert res.status_code == 201
        body = res.json()
        assert body["todo"]["title"] == "Buy groceries"
        assert body["todo"]["completed"] is False

    async def test_get_returns_created(self, client):
        """GET /api/todos should include the created todo."""
        await client.post("/api/todos", json={"title": "Walk the dog"})
        res = await client.get("/api/todos")
        assert res.status_code == 200
        todos = res.json()["todos"]
        assert len(todos) == 1
        assert todos[0]["title"] == "Walk the dog"

    async def test_get_nonexistent_id(self, client):
        """GET /api/todos/:id should 404 for unknown IDs."""
        res = await client.get("/api/todos/507f1f77bcf86cd799439011")
        assert res.status_code == 404


class TestValidation:
    async def test_missing_title(self, client):
        """POST /api/todos should reject missing title."""
        res = await client.post("/api/todos", json={})
        assert res.status_code == 400

    async def test_empty_title(self, client):
        """POST /api/todos should reject empty/whitespace title."""
        res = await client.post("/api/todos", json={"title": "   "})
        assert res.status_code == 400

    async def test_title_too_long(self, client):
        """POST /api/todos should reject titles over 200 chars."""
        res = await client.post("/api/todos", json={"title": "A" * 201})
        assert res.status_code == 400

    async def test_invalid_priority(self, client):
        """POST /api/todos should reject invalid priority values."""
        res = await client.post("/api/todos", json={"title": "X", "priority": "urgent"})
        assert res.status_code == 400

    async def test_too_many_tags(self, client):
        """POST /api/todos should reject more than 5 tags."""
        res = await client.post("/api/todos", json={"title": "X", "tags": ["a", "b", "c", "d", "e", "f"]})
        assert res.status_code == 400


class TestFiltering:
    async def test_status_active(self, client):
        """GET /api/todos?status=active should return only incomplete todos."""
        await client.post("/api/todos", json={"title": "Active 1"})
        await client.post("/api/todos", json={"title": "Active 2"})
        t3 = await client.post("/api/todos", json={"title": "Completed 1"})
        cid = t3.json()["todo"]["id"]
        await client.put(f"/api/todos/{cid}", json={"completed": True})

        res = await client.get("/api/todos?status=active")
        assert res.status_code == 200
        todos = res.json()["todos"]
        assert len(todos) == 2
        assert all(not t["completed"] for t in todos)

    async def test_search_q(self, client):
        """GET /api/todos?q=... should search in title and description."""
        await client.post("/api/todos", json={"title": "Buy milk"})
        await client.post("/api/todos", json={"title": "Walk dog"})

        res = await client.get("/api/todos?q=milk")
        assert res.status_code == 200
        todos = res.json()["todos"]
        assert len(todos) == 1
        assert "milk" in todos[0]["title"].lower()
