from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
import json
import traceback

from .. import models, schemas, duplicate_finder
from ..db import SessionLocal

router = APIRouter(prefix="/jobs", tags=["jobs"])

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def process_job(job_id: int, params: schemas.StartJobRequest):
    """
    Background task to process a duplicate-finder job.
    This function gathers video files, computes their signatures,
    finds duplicate pairs, groups them, and stores results in the database.
    It updates the job status to 'running', and finally 'done' or 'error'.
    """
    db = SessionLocal()
    try:
        # Mark job as running and set start time
        job = db.query(models.Job).get(job_id)
        if not job:
            return  # Job might have been removed or not found
        job.status = "running"
        job.started_at = datetime.utcnow()
        db.commit()  # commit early to record job started

        # Gather all video files from the specified root directories
        root_paths = [duplicate_finder.Path(r) for r in params.roots]
        videos = duplicate_finder.gather_videos(root_paths, params.exts)
        # Compute signature (frames phash sequence) for each video
        signatures = []
        for vid in videos:
            sig = duplicate_finder.signature_for(vid, params.frames, params.scale)
            signatures.append(sig)
        # Compare all signatures to find similar video pairs above threshold
        pairs_data = duplicate_finder.compare_all(signatures, params.threshold)
        # Build groups of duplicates from the pairs (cluster videos into groups)
        groups_data = duplicate_finder.build_groups(signatures, pairs_data)

        # Store pair results in the database
        pair_objects = []
        for p in pairs_data:
            a = p["a"]
            b = p["b"]
            pair_obj = models.Pair(
                job_id=job_id,
                similarity=p["similarity"],
                label=p["label"],
                file_a=a["path"],
                size_a=a.get("size", 0),
                duration_a=a.get("duration", 0.0),
                res_a=a.get("res", ""),
                file_b=b["path"],
                size_b=b.get("size", 0),
                duration_b=b.get("duration", 0.0),
                res_b=b.get("res", "")
            )
            pair_objects.append(pair_obj)
        if pair_objects:
            db.bulk_save_objects(pair_objects)
            # Alternatively: db.add_all(pair_objects)

        # Store group results in the database
        group_objects = []
        for grp in groups_data:
            files = grp["files"]
            rep_path = grp["representative"]
            total_size = grp["total_size"]
            group_obj = models.Group(
                job_id=job_id,
                representative_path=rep_path,
                count=len(files),
                total_size=total_size
            )
            # Create GroupFile entries for each file in the group
            for f in files:
                gf = models.GroupFile(
                    path=f.get("path"),
                    size=f.get("size", 0),
                    duration=f.get("duration", 0.0),
                    res=f.get("res", ""),
                    is_representative=(f.get("path") == rep_path)
                )
                group_obj.files.append(gf)
            group_objects.append(group_obj)
        if group_objects:
            # Adding group objects will also add associated GroupFile objects (cascade save-update)
            db.add_all(group_objects)

        # Update job status to done and set finished time
        job.status = "done"
        job.finished_at = datetime.utcnow()
        job.error = None
        db.commit()  # commit all changes (pairs, groups, job final status)
    except Exception as e:
        # If any error occurs, mark job as error and store the message
        db.rollback()  # rollback any partial changes
        job = db.query(models.Job).get(job_id)
        if job:
            job.status = "error"
            job.finished_at = datetime.utcnow()
            # Save error details (e.g., traceback or just error string)
            job.error = str(e)
            try:
                db.commit()
            except Exception:
                db.rollback()
        # Optionally, log the error for debugging
        traceback.print_exc()
    finally:
        db.close()

@router.get("/", response_model=list[schemas.JobOut])
def list_jobs(db: Session = Depends(get_db)):
    """Get the list of all jobs with their status and timestamps."""
    jobs = db.query(models.Job).order_by(models.Job.created_at.desc()).all()
    # Convert to Pydantic models for output
    return [schemas.JobOut.model_validate(job) for job in jobs]

@router.get("/{job_id}", response_model=schemas.JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get details of a specific job by ID."""
    job = db.query(models.Job).get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return schemas.JobOut.model_validate(job)

@router.post("/", response_model=schemas.JobOut)
def start_job(request: schemas.StartJobRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Start a new duplicate-finder job. This will queue a background task to scan the given directories
    for duplicate videos. Returns the created job info (with status 'queued').
    """
    # Create a new Job record in 'queued' status
    params_json = json.dumps(request.model_dump())  # Serialize request parameters to JSON
    new_job = models.Job(status="queued", params=params_json)
    db.add(new_job)
    db.commit()
    db.refresh(new_job)  # Refresh to get generated ID
    # Launch the duplicate search in background
    background_tasks.add_task(process_job, new_job.id, request)
    # Return the job info to the client
    return schemas.JobOut.model_validate(new_job)
