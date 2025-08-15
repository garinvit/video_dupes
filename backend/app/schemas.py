from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class StartJobRequest(BaseModel):
    roots: List[str]  # пути внутри контейнера (например /videos/dir1)
    frames: int = Field(20, ge=4, le=80)
    scale: int = Field(320, ge=0, le=1920)
    threshold: float = Field(0.88, ge=0.5, le=1.0)
    exts: List[str] = Field(default_factory=lambda: [".mp4",".mkv",".avi",".mov",".m4v",".webm",".ts",".mts",".m2ts",".wmv",".flv"])

class JobOut(BaseModel):
    id: int
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None

    class Config:
        from_attributes = True

class PairOut(BaseModel):
    id: int
    similarity: float
    label: str
    file_a: str
    size_a: int
    duration_a: float
    res_a: str
    file_b: str
    size_b: int
    duration_b: float
    res_b: str

    class Config:
        from_attributes = True

class DeleteRequest(BaseModel):
    paths: List[str]

class SizeResponse(BaseModel):
    bytes: int

# --- Groups ---
class GroupFileOut(BaseModel):
    id: int
    path: str
    size: int
    duration: float
    res: str
    is_representative: bool

    class Config:
        from_attributes = True

class GroupOut(BaseModel):
    id: int
    job_id: int
    representative_path: str
    count: int
    total_size: int
    files: List[GroupFileOut]

    class Config:
        from_attributes = True

class GroupDeleteRequest(BaseModel):
    # Если пусто — удаляем все КРОМЕ эталона
    paths: Optional[List[str]] = None