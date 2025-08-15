from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from .. import models, schemas
from ..db import SessionLocal

router = APIRouter(prefix="/jobs/{job_id}", tags=["duplicates"])

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/pairs", response_model=list[schemas.PairOut])
def get_pairs(job_id: int, db: Session = Depends(get_db)):
    """Retrieve all duplicate video pairs for a given job."""
    # Verify job exists (optional, can skip if not required)
    job = db.query(models.Job).get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    # Query all pairs associated with the job, sorted by similarity
    pairs = db.query(models.Pair).filter(models.Pair.job_id == job_id).order_by(models.Pair.similarity.desc()).all()
    return [schemas.PairOut.model_validate(p) for p in pairs]

@router.get("/groups", response_model=list[schemas.GroupOut])
def get_groups(job_id: int, db: Session = Depends(get_db)):
    """Retrieve all duplicate file groups for a given job."""
    # Verify job exists
    job = db.query(models.Job).get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    # Load groups and their files for this job (use selectinload for efficiency)
    groups = db.query(models.Group).options(selectinload(models.Group.files)).filter(models.Group.job_id == job_id).all()
    # Convert each to GroupOut (includes nested files list)
    result = []
    for g in groups:
        # Optionally sort group files so representative comes first
        g.files.sort(key=lambda f: 0 if f.is_representative else 1)
        result.append(schemas.GroupOut.model_validate(g))
    return result
