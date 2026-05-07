"""
dependencies.py
---------------
Shared FastAPI dependency-injection functions used across all routers.
"""

from typing import Generator, Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.core.security import decode_access_token
from app.models.models import JobSeeker, Company

# ---------------------------------------------------------------------------
# Database session dependency
# ---------------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    """Yields a database session and ensures it is closed after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

DB = Annotated[Session, Depends(get_db)]

# ---------------------------------------------------------------------------
# OAuth2 schemes — one per actor type
# ---------------------------------------------------------------------------
jobseeker_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/jobseeker/login")
company_oauth2_scheme   = OAuth2PasswordBearer(tokenUrl="/auth/company/login")

# ---------------------------------------------------------------------------
# Current-user dependencies
# ---------------------------------------------------------------------------
def get_current_jobseeker(
    db: DB,
    token: Annotated[str, Depends(jobseeker_oauth2_scheme)],
) -> JobSeeker:
    """Decode JWT and return the authenticated JobSeeker or raise 401."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    seeker_id: int | None = payload.get("sub")
    actor_type: str | None = payload.get("type")

    if seeker_id is None or actor_type != "jobseeker":
        raise credentials_exception

    seeker = db.query(JobSeeker).filter(JobSeeker.SeekerID == int(seeker_id)).first()
    if seeker is None:
        raise credentials_exception
    return seeker


def get_current_company(
    db: DB,
    token: Annotated[str, Depends(company_oauth2_scheme)],
) -> Company:
    """Decode JWT and return the authenticated Company or raise 401."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    company_id: int | None = payload.get("sub")
    actor_type: str  | None = payload.get("type")

    if company_id is None or actor_type != "company":
        raise credentials_exception

    company = db.query(Company).filter(Company.CompanyID == int(company_id)).first()
    if company is None:
        raise credentials_exception
    return company

# Annotated shortcuts for cleaner router signatures
CurrentSeeker  = Annotated[JobSeeker, Depends(get_current_jobseeker)]
CurrentCompany = Annotated[Company,   Depends(get_current_company)]
