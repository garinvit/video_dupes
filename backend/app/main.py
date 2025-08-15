"""Main entry for FastAPI application."""
from fastapi import FastAPI
from .routers import jobs, pairs, files  # Import routers modules

app = FastAPI(
    title="Duplicate Video Finder Backend",
    description="Backend API for searching duplicate video files",
)

# Include routers from submodules
app.include_router(jobs.router)
app.include_router(pairs.router)
app.include_router(files.router)
