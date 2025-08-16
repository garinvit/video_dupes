# backend/app/routers/jobs.py (версия с постановкой в очередь без BackgroundTasks)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import json

from .. import models, schemas
from ..db import SessionLocal

router = APIRouter(prefix="/jobs", tags=["jobs"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.JobOut)
def start_job(request: schemas.StartJobRequest, db: Session = Depends(get_db)):
    params_json = json.dumps(request.model_dump())
    new_job = models.Job(status="queued", params=params_json, created_at=datetime.utcnow())
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return schemas.JobOut.model_validate(new_job)

@router.get("/", response_model=list[schemas.JobOut])
def list_jobs(db: Session = Depends(get_db)):
    jobs = db.query(models.Job).order_by(models.Job.created_at.desc()).all()
    return [schemas.JobOut.model_validate(j) for j in jobs]

@router.get("/{job_id}", response_model=schemas.JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(models.Job).get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return schemas.JobOut.model_validate(job)

@router.get("/defaults")
def get_defaults():
    import os
    roots = os.getenv("VIDEO_ROOTS", "/videos/dir1,/videos/dir2").split(",")
    return {
        "roots": [r.strip() for r in roots if r.strip()],
        "frames": int(os.getenv("DEFAULT_FRAMES", "20")),
        "scale": int(os.getenv("DEFAULT_SCALE", "320")),
        "threshold": float(os.getenv("DEFAULT_THRESHOLD", "0.88")),
    }