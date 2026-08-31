"""
api/app.py
===========
FastAPI backend wired directly to the real Red Team / Blue Team pipeline
in this repo. No numbers are hardcoded here or in the frontend that
consumes this API -- every report endpoint reads the actual output files
on disk, live, and the pipeline endpoints trigger the actual scripts as
subprocesses.

Run (from the repo root):

    PYTHONPATH=src python3 -m uvicorn api.app:app --reload --port 8000

or, from inside api/:

    cd api && uvicorn app:app --reload --port 8000

Then open http://localhost:8000/docs for interactive API docs, or point
the dashboard frontend's fetch() calls at http://localhost:8000/api/...

CORS is left wide open (allow_origins=["*"]) because this is a local
hackathon prototype meant to be opened directly as a static HTML file
(file:// or a simple `python -m http.server`) that fetches from this
API -- tighten this before deploying anywhere real.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make `import config`, `import reports`, etc. work regardless of how
# uvicorn was launched (as `api.app:app` from repo root, or `app:app`
# from inside api/).
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402
from pydantic import BaseModel  # noqa: E402

import pipeline_runner  # noqa: E402
import reports  # noqa: E402
from config import REPORTS, STAGES  # noqa: E402

app = FastAPI(
    title="AI Defense Lab -- Red Team / Blue Team API",
    description="Backend for the Mastercard Innovation Challenge closed-loop prototype.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Report endpoints -- live reads of real output files, every call
# ---------------------------------------------------------------------------
@app.get("/api/reports/dashboard")
def get_dashboard():
    """Everything the dashboard needs in one call. Every field is a live
    disk read (see reports.dashboard_summary) -- re-run a stage and the
    very next call to this endpoint reflects it."""
    return reports.dashboard_summary()


@app.get("/api/reports/{key}")
def get_report(key: str):
    if key not in REPORTS:
        raise HTTPException(404, f"Unknown report key. Known keys: {sorted(REPORTS)}")
    path = REPORTS[key]
    if path.suffix == ".jsonl":
        return reports.read_jsonl(key)
    if path.suffix == ".json":
        return reports.read_json(key)
    raise HTTPException(400, f"Report '{key}' is not JSON/JSONL (it's {path.suffix}); use /api/reports/{key}/file")


@app.get("/api/reports/{key}/file")
def get_report_file(key: str):
    """Serve a report file as-is -- used for the SHAP PNG, and works for
    any other file-type report too."""
    if key not in REPORTS:
        raise HTTPException(404, f"Unknown report key. Known keys: {sorted(REPORTS)}")
    path = REPORTS[key]
    if not path.exists():
        raise HTTPException(404, f"{path.name} hasn't been generated yet -- run the pipeline first.")
    return FileResponse(path)


# ---------------------------------------------------------------------------
# Pipeline control
# ---------------------------------------------------------------------------
@app.get("/api/pipeline/stages")
def get_stages():
    """Static catalog of what the closed loop consists of -- lets the
    frontend render the pipeline diagram without hardcoding it too."""
    return {"stages": STAGES}


class RunRequest(BaseModel):
    stage_ids: list[str] | None = None  # None = run all stages, in order


@app.post("/api/pipeline/run")
def run_pipeline(req: RunRequest):
    try:
        job_id = pipeline_runner.start_run(req.stage_ids)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"job_id": job_id}


@app.get("/api/pipeline/status/{job_id}")
def pipeline_status(job_id: str):
    job = pipeline_runner.get_job(job_id)
    if job is None:
        raise HTTPException(404, "Unknown job_id")
    return job


@app.get("/api/pipeline/jobs")
def pipeline_jobs():
    return {"jobs": pipeline_runner.list_jobs()}
