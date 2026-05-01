"""Sanity checks — visible to students.

These run against the docker compose stack.
Start with: docker compose up --build -d
"""

import subprocess
import time

import pytest
import requests

BASE = "http://localhost:8080"


@pytest.fixture(scope="module", autouse=True)
def compose_stack():
    """Start docker compose stack for testing."""
    subprocess.run(
        ["docker", "compose", "up", "--build", "-d"],
        check=True,
        capture_output=True,
        timeout=120,
    )
    # Wait for API to be ready
    for _ in range(30):
        try:
            resp = requests.get(f"{BASE}/health", timeout=2)
            if resp.status_code == 200:
                break
        except (requests.ConnectionError, requests.Timeout):
            time.sleep(2)
    yield
    subprocess.run(["docker", "compose", "down", "-v"], capture_output=True)


def test_health():
    resp = requests.get(f"{BASE}/health", timeout=5)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


def test_register_and_get_node():
    resp = requests.post(
        f"{BASE}/api/nodes",
        json={"name": "sanity-node", "host": "10.0.0.1", "port": 3000},
        timeout=5,
    )
    assert resp.status_code == 201

    resp = requests.get(f"{BASE}/api/nodes/sanity-node", timeout=5)
    assert resp.status_code == 200
    assert resp.json()["name"] == "sanity-node"


def test_list_nodes():
    resp = requests.get(f"{BASE}/api/nodes", timeout=5)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
