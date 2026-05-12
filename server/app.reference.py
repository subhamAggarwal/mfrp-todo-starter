"""Reference solution for the Python Todo API.

This is the complete, working implementation that passes all hidden tests.
Use it to validate the hidden-test bundle before publishing the question.
"""

import os
import re
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from pymongo import MongoClient
from pymongo.collection import Collection
from bson import ObjectId

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

_client = None
_db = None


def connect(uri: Optional[str] = None):
    global _client, _db
    _client = MongoClient(uri or os.environ.get("MONGODB_URI", "mongodb://localhost:27017/todos"))
    _db = _client.get_default_database()


def disconnect():
    global _client
    if _client:
        _client.close()
        _client = None


def get_todos_collection() -> Collection:
    return _db["todos"]


# ---------------------------------------------------------------------------
# Models (with full validation)
# ---------------------------------------------------------------------------

class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    priority: Optional[str] = "medium"
    dueDate: Optional[str] = None
    tags: Optional[List[str]] = []
    position: Optional[int] = 0

    @field_validator("priority")
    @classmethod
    def check_priority(cls, v):
        if v not in ("low", "medium", "high"):
            raise ValueError("Priority must be one of: low, medium, high")
        return v

    @field_validator("dueDate")
    @classmethod
    def check_due_date(cls, v):
        if v is None:
            return None
        try:
            datetime.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError("Invalid dueDate")

    @field_validator("tags")
    @classmethod
    def check_tags(cls, v):
        if v is not None and len(v) > 5:
            raise ValueError("Tags can have at most 5 entries")
        return v

    @field_validator("position")
    @classmethod
    def check_position(cls, v):
        if v is not None and v < 0:
            raise ValueError("Position must be non-negative")
        return v


class TodoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
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
    todo = dict(doc)
    todo["id"] = str(todo.pop("_id"))
    for key in ("createdAt", "updatedAt", "dueDate"):
        if key in todo and todo[key] is not None:
            val = todo[key]
            if isinstance(val, datetime):
                todo[key] = val.isoformat()
    return todo


def build_query(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    q: Optional[str] = None,
    sort: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    mongo_query = {}

    if status == "active":
        mongo_query["completed"] = False
    elif status == "completed":
        mongo_query["completed"] = True
    elif status is not None:
        raise HTTPException(status_code=400, detail="Invalid status filter")

    if priority:
        mongo_query["priority"] = priority

    if q:
        mongo_query["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
        ]

    sort_option = [("createdAt", 1)]
    if sort == "createdAt":
        sort_option = [("createdAt", 1)]

    return mongo_query, sort_option, limit, offset


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
        mongo_query, sort_opt, lim, off = build_query(status, priority, q, sort, limit, offset)
        cursor = (
            get_todos_collection()
            .find(mongo_query)
            .sort(sort_opt)
            .skip(off)
            .limit(lim)
        )
        return {"todos": [doc_to_todo(d) for d in cursor]}

    @app.post("/api/todos", status_code=201)
    def create_todo(data: TodoCreate):
        collection = get_todos_collection()
        now = datetime.utcnow()
        doc = {
            "title": data.title.strip(),
            "description": data.description.strip() if data.description else None,
            "completed": False,
            "priority": data.priority,
            "dueDate": datetime.fromisoformat(data.dueDate) if data.dueDate else None,
            "tags": data.tags or [],
            "position": data.position if data.position is not None else 0,
            "createdAt": now,
            "updatedAt": now,
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
        if not is_valid_object_id(todo_id):
            raise HTTPException(status_code=404, detail="Todo not found")

        update_fields = {}
        if data.title is not None:
            update_fields["title"] = data.title.strip()
        if data.description is not None:
            update_fields["description"] = data.description.strip() if data.description else None
        if data.priority is not None:
            update_fields["priority"] = data.priority
        if data.dueDate is not None:
            update_fields["dueDate"] = datetime.fromisoformat(data.dueDate) if data.dueDate else None
        if data.tags is not None:
            update_fields["tags"] = data.tags
        if data.position is not None:
            update_fields["position"] = data.position
        if data.completed is not None:
            update_fields["completed"] = data.completed

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        result = get_todos_collection().find_one_and_update(
            {"_id": ObjectId(todo_id)},
            {"$set": {**update_fields, "updatedAt": datetime.utcnow()}},
            return_document=True,
        )
        if not result:
            raise HTTPException(status_code=404, detail="Todo not found")
        return {"todo": doc_to_todo(result)}

    @app.patch("/api/todos/{todo_id}/toggle")
    def toggle_todo(todo_id: str):
        if not is_valid_object_id(todo_id):
            raise HTTPException(status_code=404, detail="Todo not found")
        doc = get_todos_collection().find_one({"_id": ObjectId(todo_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Todo not found")
        new_status = not doc.get("completed", False)
        result = get_todos_collection().find_one_and_update(
            {"_id": ObjectId(todo_id)},
            {"$set": {"completed": new_status, "updatedAt": datetime.utcnow()}},
            return_document=True,
        )
        return {"todo": doc_to_todo(result)}

    @app.delete("/api/todos/{todo_id}")
    def delete_todo(todo_id: str):
        if not is_valid_object_id(todo_id):
            raise HTTPException(status_code=404, detail="Todo not found")
        result = get_todos_collection().delete_one({"_id": ObjectId(todo_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Todo not found")
        return {"todo": {"id": todo_id}}

    @app.delete("/api/todos")
    def bulk_delete(status: Optional[str] = Query(None)):
        if status == "completed":
            result = get_todos_collection().delete_many({"completed": True})
            return {"deletedCount": result.deleted_count}
        else:
            raise HTTPException(status_code=400, detail="Invalid status")

    @app.post("/api/todos/reorder")
    def reorder_todos(items: List[dict]):
        if not isinstance(items, list):
            raise HTTPException(status_code=400, detail="items must be an array")

        collection = get_todos_collection()

        for item in items:
            todo_id = item.get("id")
            position = item.get("position")

            if not todo_id or not is_valid_object_id(todo_id):
                raise HTTPException(status_code=400, detail="Invalid todo id")
            if position is None or position < 0:
                raise HTTPException(status_code=400, detail="Position must be non-negative")

            exists = collection.find_one({"_id": ObjectId(todo_id)})
            if not exists:
                raise HTTPException(status_code=404, detail="Todo not found")

        for item in items:
            collection.update_one(
                {"_id": ObjectId(item["id"])},
                {"$set": {"position": item["position"], "updatedAt": datetime.utcnow()}}
            )

        return {"todos": [doc_to_todo(d) for d in collection.find().sort("position", 1)]}

    return app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(create_app(), host="0.0.0.0", port=3000)
