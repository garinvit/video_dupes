from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path
import base64
import random

from .. import models, schemas, duplicate_finder
from ..db import SessionLocal

router = APIRouter(prefix="/files", tags=["files"])

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/frames")
def get_video_frames(path: str, count: int = 3, scale: int = 320):
    """
    Extract multiple frames from the given video file.
    Returns a JSON with base64-encoded JPEG images for preview.
    """
    video_path = Path(path)
    if not video_path.is_file():
        raise HTTPException(status_code=404, detail="Video file not found")
    # Use ffprobe to get video duration (seconds)
    duration, _, _ = duplicate_finder.ffprobe(video_path)
    if duration <= 0:
        raise HTTPException(status_code=400, detail="Could not get video duration or video has no content")
    # Determine frame timestamps (randomly select `count` timestamps within video duration)
    frame_times = []
    for _ in range(count):
        t = random.uniform(0, max(0.0, duration - 0.1))
        frame_times.append(t)
    # Extract frames using ffmpeg for each timestamp
    encoded_frames = []
    for t in frame_times:
        # Prepare ffmpeg command to capture a frame at time t
        vf_filter = f"scale={scale}:-2" if scale and scale > 0 else "null"
        cmd = [
            "ffmpeg", "-ss", f"{t:.3f}", "-i", str(video_path),
            "-frames:v", "1", "-vf", vf_filter,
            "-f", "image2pipe", "-vcodec", "mjpeg",
            "-loglevel", "error", "pipe:1"
        ]
        try:
            frame_bytes = duplicate_finder.subprocess.check_output(cmd, stderr=duplicate_finder.subprocess.STDOUT)
        except duplicate_finder.subprocess.CalledProcessError:
            continue  # skip this frame on error (e.g., timestamp beyond video length)
        # Encode the frame bytes to a base64 string
        b64_str = base64.b64encode(frame_bytes).decode('utf-8')
        encoded_frames.append(b64_str)
    return {"frames": encoded_frames}

def _delete_files(paths: list[str], db: Session) -> int:
    """
    Helper function to delete files from filesystem and remove their records from the database.
    Returns the total size (in bytes) of files deleted.
    """
    total_bytes = 0
    deleted_paths = []
    for file_path in paths:
        try:
            p = Path(file_path)
            if p.is_file():
                size = p.stat().st_size
                p.unlink()  # delete the file from disk
                total_bytes += size
                deleted_paths.append(file_path)
            else:
                # If file does not exist, treat as already deleted (remove from DB if present)
                deleted_paths.append(file_path)
        except Exception:
            # Skip files that cannot be deleted (e.g., permission issues)
            continue
    if not deleted_paths:
        return 0
    # Remove database entries for deleted files
    # Remove GroupFile entries for these paths
    group_files = db.query(models.GroupFile).filter(models.GroupFile.path.in_(deleted_paths)).all()
    affected_group_ids = {gf.group_id for gf in group_files}
    for gf in group_files:
        db.delete(gf)
    # Remove Pair entries that reference these files
    db.query(models.Pair).filter((models.Pair.file_a.in_(deleted_paths)) | (models.Pair.file_b.in_(deleted_paths))).delete(synchronize_session=False)
    # Update or remove affected groups after deletion
    for gid in affected_group_ids:
        group = db.query(models.Group).get(gid)
        if not group:
            continue
        # Query remaining files in this group
        remaining_files = db.query(models.GroupFile).filter(models.GroupFile.group_id == gid).all()
        if len(remaining_files) < 2:
            # If fewer than 2 files remain, remove the group entirely (no duplicates left)
            db.delete(group)
        else:
            # If the group still has 2 or more files, update representative if needed
            if group.representative_path in deleted_paths:
                # Choose a new representative (max duration, then resolution, then size)
                def res_value(res: str):
                    try:
                        w, h = res.lower().split('x')
                        return int(w) * int(h)
                    except Exception:
                        return 0
                best_file = max(remaining_files, key=lambda f: ((f.duration or 0), res_value(f.res or ""), (f.size or 0)))
                group.representative_path = best_file.path
                # Update is_representative flags for files in this group
                for f in remaining_files:
                    f.is_representative = (f.path == best_file.path)
            # Recalculate count and total_size for the group
            group.count = len(remaining_files)
            group.total_size = sum((f.size or 0) for f in remaining_files)
    return total_bytes

@router.post("/delete", response_model=schemas.SizeResponse)
def delete_files(request: schemas.DeleteRequest, db: Session = Depends(get_db)):
    """
    Delete the specified files from disk and remove their records from the database.
    Returns the total bytes freed.
    """
    if not request.paths:
        # No files specified
        return {"bytes": 0}
    total_bytes = _delete_files(request.paths, db)
    db.commit()  # commit changes (deletions and updates)
    return {"bytes": total_bytes}

@router.post("/groups/{group_id}/delete", response_model=schemas.SizeResponse)
def delete_group_files(group_id: int, request: schemas.GroupDeleteRequest, db: Session = Depends(get_db)):
    """
    Delete files in a duplicate group. If a list of paths is provided, deletes those files from the group.
    If no list is provided, deletes all files in the group except the representative file.
    Returns the total bytes freed.
    """
    # Fetch group and its files
    group = db.query(models.Group).get(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    group_files = db.query(models.GroupFile).filter(models.GroupFile.group_id == group_id).all()
    if not group_files:
        return {"bytes": 0}
    # Determine which files to delete
    if request.paths is not None and len(request.paths) > 0:
        # Only delete specified paths (ensure they belong to this group)
        group_paths = {gf.path for gf in group_files}
        to_delete = [p for p in request.paths if p in group_paths]
    else:
        # Delete all non-representative files in the group
        to_delete = [gf.path for gf in group_files if not gf.is_representative]
    if not to_delete:
        return {"bytes": 0}
    total_bytes = _delete_files(to_delete, db)
    db.commit()
    return {"bytes": total_bytes}
