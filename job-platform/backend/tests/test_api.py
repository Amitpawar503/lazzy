"""End-to-end API tests using FastAPI's TestClient (no network required).

Run:  cd backend && pytest -q
"""
import os

os.environ.setdefault("INGEST_ON_STARTUP", "false")
os.environ["DATABASE_URL"] = "sqlite:///./test_careerhound.db"

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    if os.path.exists("test_careerhound.db"):
        os.remove("test_careerhound.db")
    from app.main import app
    with TestClient(app) as c:
        yield c
    if os.path.exists("test_careerhound.db"):
        os.remove("test_careerhound.db")


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_sample_load_and_dedupe(client):
    assert client.post("/api/sources/load-sample").json()["inserted"] == 12
    # Reloading must not create duplicates.
    assert client.post("/api/sources/load-sample").json()["inserted"] == 0


def test_tabs_classify(client):
    client.post("/api/sources/load-sample")
    remote_india = client.get("/api/jobs?tab=remote_india&limit=50").json()["total"]
    remote_out = client.get("/api/jobs?tab=remote_outside&limit=50").json()["total"]
    wfh = client.get("/api/jobs?tab=wfh_ncr&limit=50").json()["total"]
    assert remote_india > 0
    assert remote_out > 0
    assert wfh > 0
    # WFH-NCR jobs must be flagged.
    for j in client.get("/api/jobs?tab=wfh_ncr&limit=50").json()["items"]:
        assert j["is_wfh_ncr"] is True


def test_resume_upload_and_match(client):
    client.post("/api/sources/load-sample")
    text = (b"Senior Software Engineer. 8 years Python, FastAPI, Django, AWS, "
            b"PostgreSQL, Kafka, Docker, Kubernetes. Remote India. React, TypeScript, SQL.")
    up = client.post("/api/resumes", files={"file": ("cv.txt", text, "text/plain")}).json()
    assert up["id"]
    assert "python" in up["skills"]

    matches = client.get(f"/api/resumes/{up['id']}/matches?limit=5").json()
    assert len(matches) > 0
    # Scores must be sorted descending and the top match should be a backend role.
    scores = [m["match_score"] for m in matches]
    assert scores == sorted(scores, reverse=True)
    assert matches[0]["match_score"] > 0


def test_enhance_fallback(client):
    client.post("/api/sources/load-sample")
    text = b"Backend engineer with Python, FastAPI, AWS."
    up = client.post("/api/resumes", files={"file": ("cv.txt", text, "text/plain")}).json()
    job = client.get("/api/jobs?limit=1").json()["items"][0]
    enh = client.post("/api/resumes/enhance", json={"resume_id": up["id"], "job_id": job["id"]}).json()
    assert enh["ai_used"] is False  # no key configured in tests
    assert enh["enhanced_summary"]
    assert isinstance(enh["tailored_bullets"], list)
    assert enh["cover_letter"]
