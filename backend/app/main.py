from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import jobs, pairs, files

app = FastAPI(
    title="Duplicate Video Finder Backend",
    description="Backend API for searching duplicate video files",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router)
app.include_router(pairs.router)
app.include_router(files.router)
