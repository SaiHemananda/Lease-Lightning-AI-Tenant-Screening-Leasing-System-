# backend/services.py
import json
from pathlib import Path
from threading import Lock
from datetime import datetime
import asyncio

from backend.config.settings import DATA_DIR

DATA_FILE = DATA_DIR / "applicants.json"
_lock = Lock()

# seed default (same as your Streamlit file)
DEFAULTS = [
    {"id": 1001, "name": "Anya Sharma", "unit": "402B", "date": "2025-11-19", "status": "Decision Ready", "risk": "Low", "income_match": "110%", "error_rate": "0%"},
    {"id": 1002, "name": "Ben Carter", "unit": "105A", "date": "2025-11-18", "status": "Verification Agent", "risk": "Pending", "income_match": "Pending", "error_rate": "N/A"},
    {"id": 1003, "name": "Chloe Davis", "unit": "512C", "date": "2025-11-17", "status": "Decision Ready", "risk": "Medium", "income_match": "85%", "error_rate": "0%"},
    {"id": 1004, "name": "David Lee", "unit": "201B", "date": "2025-11-15", "status": "Document Agent", "risk": "Low", "income_match": "125%", "error_rate": "0%"},
    {"id": 1005, "name": "Eva Rodriguez", "unit": "308D", "date": "2025-11-14", "status": "Denied", "risk": "High", "income_match": "60%", "error_rate": "N/A"},
]

def _read():
    if not DATA_FILE.exists():
        with DATA_FILE.open("w") as f:
            json.dump(DEFAULTS, f, indent=2)
        return DEFAULTS.copy()
    with DATA_FILE.open("r") as f:
        return json.load(f)

def _write(data):
    with DATA_FILE.open("w") as f:
        json.dump(data, f, indent=2)

def list_applicants():
    with _lock:
        return _read()

def get_applicant(app_id):
    with _lock:
        data = _read()
        for a in data:
            if a["id"] == app_id:
                return a
    return None

def create_applicant(name, unit):
    with _lock:
        data = _read()
        new_id = max((a["id"] for a in data), default=1000) + 1
        new = {
            "id": new_id,
            "name": name,
            "unit": unit,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "status": "Submitted/Manual",
            "risk": "Pending",
            "income_match": "N/A",
            "error_rate": "N/A",
        }
        data.append(new)
        _write(data)
        return new

def update_applicant(app_id, updates: dict):
    with _lock:
        data = _read()
        for i, a in enumerate(data):
            if a["id"] == app_id:
                for k, v in updates.items():
                    if v is not None:
                        a[k] = v
                data[i] = a
                _write(data)
                return a
    return None

def delete_applicant(app_id):
    with _lock:
        data = _read()
        new = [a for a in data if a["id"] != app_id]
        if len(new) == len(data):
            return False
        _write(new)
        return True

# ---- Agent / Background work ----
async def _mock_decision_engine(applicant):
    # simulate async I/O (LLM calls, external checks)
    await asyncio.sleep(2)  # demo delay
    # simple deterministic rule for demo
    risk = "Low" if applicant["id"] % 2 == 0 else "Medium"
    return {"status": "Decision Ready", "risk": risk, "note": f"Processed at {datetime.utcnow().isoformat()}"}

def enqueue_decision_agent(background_tasks, applicant_id: int):
    # schedule the coroutine in background via asyncio.run in a separate task
    async def task():
        applicant = get_applicant(applicant_id)
        if not applicant:
            return
        res = await _mock_decision_engine(applicant)
        # update DB after processing
        update_applicant(applicant_id, {"status": res["status"], "risk": res["risk"]})

    # run the task non-blocking for FastAPI request handling
    background_tasks.add_task(asyncio.run, task())
