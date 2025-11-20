# backend/api.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel
from backend import services

router = APIRouter(prefix="/api", tags=["applicants"])

# Pydantic models
class ApplicantCreate(BaseModel):
    name: str
    unit: Optional[str] = ""

class ApplicantUpdate(BaseModel):
    status: Optional[str] = None
    risk: Optional[str] = None

class ApplicantResponse(BaseModel):
    id: int
    name: str
    unit: str
    date: str
    status: str
    risk: str
    income_match: str
    error_rate: str

# Endpoints
@router.get("/applicants", response_model=List[ApplicantResponse])
def list_applicants():
    return services.list_applicants()

@router.get("/applicants/{app_id}", response_model=ApplicantResponse)
def get_applicant(app_id: int):
    app = services.get_applicant(app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Applicant not found")
    return app

@router.post("/applicants", response_model=ApplicantResponse, status_code=201)
def create_applicant(payload: ApplicantCreate):
    return services.create_applicant(payload.name, payload.unit or "")

@router.patch("/applicants/{app_id}", response_model=ApplicantResponse)
def patch_applicant(app_id: int, payload: ApplicantUpdate):
    updated = services.update_applicant(app_id, payload.dict())
    if not updated:
        raise HTTPException(status_code=404, detail="Applicant not found")
    return updated

@router.delete("/applicants/{app_id}", status_code=204)
def delete_applicant(app_id: int):
    ok = services.delete_applicant(app_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Applicant not found")
    return

@router.post("/applicants/{app_id}/run-decision")
def run_decision(app_id: int, background_tasks: BackgroundTasks):
    if not services.get_applicant(app_id):
        raise HTTPException(status_code=404, detail="Applicant not found")
    services.enqueue_decision_agent(background_tasks, app_id)
    return {"status": "queued", "applicant_id": app_id}
