# backend/app/worker.py
import os
import time
import json
import traceback
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from .db import SessionLocal, engine
from . import models, duplicate_finder

POLL_INTERVAL = float(os.getenv("WORKER_POLL_INTERVAL", "2.0"))

def _take_job(session: Session) -> models.Job | None:
    """
    Берём одно задание в статусе queued с блокировкой, обновляем на running.
    Используем SKIP LOCKED, чтобы несколько воркеров не взяли одно и то же.
    """
    # raw SQL, потому что с ORM длиннее. Работает в PostgreSQL.
    job_row = session.execute(text("""
        SELECT id FROM jobs
        WHERE status = 'queued'
        ORDER BY created_at
        FOR UPDATE SKIP LOCKED
        LIMIT 1
    """)).first()
    if not job_row:
        return None
    job = session.get(models.Job, job_row[0], with_for_update=True)
    job.status = "running"
    job.started_at = datetime.utcnow()
    session.commit()
    session.refresh(job)
    return job

def _process_job(session: Session, job: models.Job):
    params = json.loads(job.params)
    roots = [duplicate_finder.Path(p) for p in params["roots"]]
    frames = int(params.get("frames", 20))
    scale = int(params.get("scale", 320))
    threshold = float(params.get("threshold", 0.88))
    exts = params.get("exts") or list(duplicate_finder.VIDEO_EXTS)

    videos = duplicate_finder.gather_videos(roots, exts)
    signs = [duplicate_finder.signature_for(v, frames, scale) for v in videos]
    pairs = duplicate_finder.compare_all(signs, threshold)
    groups = duplicate_finder.build_groups(signs, pairs)

    # Сохраняем пары
    pair_objs = []
    for p in pairs:
        a, b = p["a"], p["b"]
        pair_objs.append(models.Pair(
            job_id=job.id,
            similarity=p["similarity"],
            label=p["label"],
            file_a=a["path"], size_a=a.get("size", 0),
            duration_a=a.get("duration", 0.0), res_a=a.get("res", ""),
            file_b=b["path"], size_b=b.get("size", 0),
            duration_b=b.get("duration", 0.0), res_b=b.get("res", ""),
        ))
    if pair_objs:
        session.bulk_save_objects(pair_objs)

    # Сохраняем группы
    for g in groups:
        grp = models.Group(
            job_id=job.id,
            representative_path=g["representative"],
            count=len(g["files"]),
            total_size=g["total_size"],
        )
        for f in g["files"]:
            grp.files.append(models.GroupFile(
                path=f.get("path"),
                size=f.get("size", 0),
                duration=f.get("duration", 0.0),
                res=f.get("res", ""),
                is_representative=(f.get("path") == g["representative"]),
            ))
        session.add(grp)

    job.status = "done"
    job.finished_at = datetime.utcnow()
    job.error = None
    session.commit()

def run_worker():
    while True:
        session = SessionLocal()
        try:
            job = _take_job(session)
            if not job:
                time.sleep(POLL_INTERVAL)
                continue
            try:
                _process_job(session, job)
            except Exception as e:
                session.rollback()
                j = session.get(models.Job, job.id)
                if j:
                    j.status = "error"
                    j.finished_at = datetime.utcnow()
                    j.error = str(e)
                    session.commit()
                traceback.print_exc()
        finally:
            session.close()

if __name__ == "__main__":
    run_worker()
