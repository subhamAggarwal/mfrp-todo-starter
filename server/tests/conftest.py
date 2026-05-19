"""Pytest fixtures for visible backend tests.

Uses mongodb-memory-server (via pymongo) or an in-memory mongod.
"""

import glob
import os
import subprocess
import tempfile
import time

import pytest
from pymongo import MongoClient


def _find_mongod() -> str | None:
    """Discover any pre-baked mongod binary in the cache directory."""
    cache_dir = "/home/coder/.cache/mongodb-binaries"
    candidates = glob.glob(os.path.join(cache_dir, "mongod*"))
    for c in candidates:
        if os.path.isfile(c) and not c.endswith(".md5"):
            return c
    return None


def _wait_for_mongo(uri: str, timeout: float = 30.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            client = MongoClient(uri, serverSelectionTimeoutMS=2000)
            client.admin.command("ping")
            client.close()
            return True
        except Exception:
            time.sleep(0.5)
    return False


@pytest.fixture(scope="session")
def mongod():
    """Start an ephemeral mongod process."""
    import shutil
    binary = _find_mongod()
    if not binary:
        pytest.skip("mongod binary not found (run npm run prefetch:mongo)")

    db_path = tempfile.mkdtemp(prefix="mongo-mem-")
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]

    proc = subprocess.Popen(
        [binary, "--port", str(port), "--dbpath", db_path,
         "--storageEngine", "ephemeralForTest", "--bind_ip", "127.0.0.1", "--noauth"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )

    uri = f"mongodb://127.0.0.1:{port}/test"
    if not _wait_for_mongo(uri, timeout=30):
        proc.terminate()
        proc.wait()
        shutil.rmtree(db_path, ignore_errors=True)
        pytest.skip("mongod failed to start")

    os.environ["MONGODB_URI"] = uri
    yield uri

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    shutil.rmtree(db_path, ignore_errors=True)


@pytest.fixture(scope="session")
def app(mongod):
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from app import create_app, connect, disconnect
    connect(mongod)
    yield create_app()
    disconnect()


@pytest.fixture
async def client(app):
    import httpx
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.fixture(autouse=True)
def clean_db(mongod):
    mongo_client = MongoClient(mongod, serverSelectionTimeoutMS=5000)
    mongo_client["test"]["todos"].drop()
    mongo_client.close()
    yield
