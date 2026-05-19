"""FastAPI Todo app — candidate starter.

Implement the REST endpoints below so the hidden-test suite and React
frontend work correctly. Some endpoints are already wired; others have
# TODO comments for you to fill in.

The app factory `create_app()` is imported by the hidden tests.
"""

import os
import re
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from pymongo import MongoClient
from pymongo.collection import Collection
from bson import ObjectId

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

_client = None
_db = None


def connect(uri: Optional[str] = None):
    """Connect to MongoDB (called once in lifespan)."""
    global _client, _db
    _client = MongoClient(uri or os.environ.get("MONGODB_URI", "mongodb://localhost:27017/todos"))
    _db = _client.get_default_database()


def disconnect():
    """Disconnect from MongoDB."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
    _db = None


def get_todos_collection() -> Collection:
    return _db["todos"]


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Optional[str] = "medium"
    dueDate: Optional[str] = None
    tags: Optional[List[str]] = []
    position: Optional[int] = 0


class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    dueDate: Optional[str] = None
    tags: Optional[List[str]] = None
    position: Optional[int] = None
    completed: Optional[bool] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

OBJECT_ID_RE = re.compile(r"^[0-9a-fA-F]{24}$")


def is_valid_object_id(oid: str) -> bool:
    return bool(OBJECT_ID_RE.fullmatch(oid))


def doc_to_todo(doc) -> dict:
    """Transform a MongoDB document into the public API shape."""
    todo = dict(doc)
    todo["id"] = str(todo.pop("_id"))
    for key in ("createdAt", "updatedAt", "dueDate"):
        if key in todo and todo[key] is not None:
            val = todo[key]
            if isinstance(val, datetime):
                todo[key] = val.isoformat()
    return todo


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    connect()
    yield
    disconnect()


def create_app() -> FastAPI:
    app = FastAPI(title="Todos API", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=400, content={"detail": exc.errors()})

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/todos")
    def list_todos(
        status: Optional[str] = Query(None),
        priority: Optional[str] = Query(None),
        q: Optional[str] = Query(None),
        sort: Optional[str] = Query(None),
        limit: int = Query(100, ge=1),
        offset: int = Query(0, ge=0),
    ):
        # TODO: implement filtering, sorting, and pagination
        cursor = get_todos_collection().find({}).sort("createdAt", 1).skip(offset).limit(limit)
        return {"todos": [doc_to_todo(d) for d in cursor]}

    @app.post("/api/todos", status_code=201)
    def create_todo(data: TodoCreate):
        collection = get_todos_collection()

        # Validation
        if not data.title or not data.title.strip():
            raise HTTPException(status_code=400, detail="Title is required and must be a non-empty string")

        # TODO: add validation for max length, priority, dueDate, tags, position

        doc = {
            "title": data.title.strip(),
            "description": data.description.strip() if data.description else None,
            "completed": False,
            "priority": data.priority or "medium",
            "dueDate": datetime.fromisoformat(data.dueDate) if data.dueDate else None,
            "tags": data.tags or [],
            "position": data.position if data.position is not None else 0,
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow(),
        }
        result = collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return {"todo": doc_to_todo(doc)}

    @app.get("/api/todos/{todo_id}")
    def get_todo(todo_id: str):
        if not is_valid_object_id(todo_id):
            raise HTTPException(status_code=404, detail="Todo not found")
        doc = get_todos_collection().find_one({"_id": ObjectId(todo_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Todo not found")
        return {"todo": doc_to_todo(doc)}

    @app.put("/api/todos/{todo_id}")
    def update_todo(todo_id: str, data: TodoUpdate):
        # TODO: implement update with validation
        raise HTTPException(status_code=501, detail="Not implemented")

    @app.patch("/api/todos/{todo_id}/toggle")
    def toggle_todo(todo_id: str):
        # TODO: implement toggle
        raise HTTPException(status_code=501, detail="Not implemented")

    @app.delete("/api/todos/{todo_id}")
    def delete_todo(todo_id: str):
        # TODO: implement delete
        raise HTTPException(status_code=501, detail="Not implemented")

    @app.delete("/api/todos")
    def bulk_delete(status: Optional[str] = Query(None)):
        # TODO: implement bulk delete
        raise HTTPException(status_code=501, detail="Not implemented")

    @app.post("/api/todos/reorder")
    def reorder_todos(items: List[dict]):
        # TODO: implement reorder
        raise HTTPException(status_code=501, detail="Not implemented")

    return app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(create_app(), host="0.0.0.0", port=3000)
