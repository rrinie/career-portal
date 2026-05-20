"""
main.py
-------
FastAPI application entry point.

Run with:
    uvicorn app.main:app --reload --port 8002

Swagger UI:   http://localhost:8002/docs
ReDoc:        http://localhost:8002/redoc
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, jobseekers, companies, jobs, applications, interviews


# ---------------------------------------------------------------------------
# App initialisation  — MUST come before any app.include_router() call
# ---------------------------------------------------------------------------
app = FastAPI(
    title="University Career Portal API",
    description=(
        "Backend for the University Career Portal.\n\n"
        "**Two actor types, two JWT flows:**\n"
        "- **JobSeeker** — register/login at `/auth/jobseeker/*`\n"
        "- **Company**   — register/login at `/auth/company/*`\n\n"
        "Authorise in Swagger UI using the lock icon before calling protected endpoints."
    ),
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ---------------------------------------------------------------------------
# Routers  — registered in dependency order
# ---------------------------------------------------------------------------
app.include_router(auth.router)           # /auth/*
app.include_router(jobseekers.router)     # /jobseekers/*
app.include_router(companies.router)      # /companies/*
app.include_router(jobs.router)           # /jobs/*
app.include_router(applications.router)   # /applications/*
app.include_router(interviews.router)     # /interviews/*


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "Career Portal API is running."}
