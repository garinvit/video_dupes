from fastapi import APIRouter, Depends, HTTPException, Response, Query
from sqlalchemy.orm import Session, selectinload

from .. import models, schemas
from ..db import SessionLocal

router = APIRouter(prefix="/jobs/{job_id}", tags=["duplicates"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/pairs", response_model=list[schemas.PairOut])
def get_pairs(
    job_id: int,
    response: Response,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Пары с пагинацией. Возвращает X-Total-Count.
    """
    job = db.query(models.Job).get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    q = db.query(models.Pair).filter(models.Pair.job_id == job_id)
    total = q.count()
    pairs = (
        q.order_by(models.Pair.similarity.desc())
         .limit(limit).offset(offset)
         .all()
    )
    response.headers["X-Total-Count"] = str(total)
    return [schemas.PairOut.model_validate(p) for p in pairs]

@router.get("/groups", response_model=list[schemas.GroupOut])
def get_groups(
    job_id: int,
    response: Response,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Группы с пагинацией. Возвращает X-Total-Count.
    """
    job = db.query(models.Job).get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    base = db.query(models.Group).filter(models.Group.job_id == job_id)
    total = base.count()
    groups = (
        base.order_by(models.Group.id.asc())
            .limit(limit).offset(offset)
            .options(selectinload(models.Group.files))
            .all()
    )
    result = []
    for g in groups:
        g.files.sort(key=lambda f: 0 if f.is_representative else 1)
        result.append(schemas.GroupOut.model_validate(g))
    response.headers["X-Total-Count"] = str(total)
    return result
