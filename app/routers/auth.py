"""
Authentication endpoints for JobSeeker and Company actors.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.security import create_access_token, hash_password, verify_password
from app.dependencies import DB
from app.models.models import Company, JobSeeker
from app.schemas.auth import Token
from app.schemas.company import CompanyCreate, CompanyOut
from app.schemas.jobseeker import JobSeekerCreate, JobSeekerOut

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post(
    "/jobseeker/register",
    response_model=JobSeekerOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a JobSeeker",
)
def register_jobseeker(payload: JobSeekerCreate, db: DB):
    existing = db.query(JobSeeker).filter(JobSeeker.Email == payload.Email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A JobSeeker with this email already exists.",
        )

    seeker = JobSeeker(
        FirstName=payload.FirstName,
        LastName=payload.LastName,
        Email=str(payload.Email),
        PasswordHash=hash_password(payload.Password),
        Phone=payload.Phone,
    )
    db.add(seeker)
    db.commit()
    db.refresh(seeker)
    return seeker


@router.post(
    "/jobseeker/login",
    response_model=Token,
    summary="Log in as a JobSeeker",
)
def login_jobseeker(
    db: DB,
    form: OAuth2PasswordRequestForm = Depends(),
):
    seeker = db.query(JobSeeker).filter(JobSeeker.Email == form.username).first()
    if seeker is None or not verify_password(form.password, seeker.PasswordHash):
        raise _unauthorized()

    return Token(
        access_token=create_access_token(seeker.SeekerID, "jobseeker"),
        token_type="bearer",
    )


@router.post(
    "/company/register",
    response_model=CompanyOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a Company",
)
def register_company(payload: CompanyCreate, db: DB):
    existing = db.query(Company).filter(Company.ContactEmail == payload.ContactEmail).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A Company with this contact email already exists.",
        )

    company = Company(
        CompanyName=payload.CompanyName,
        Industry=payload.Industry,
        City=payload.City,
        ContactEmail=str(payload.ContactEmail),
        PasswordHash=hash_password(payload.Password),
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.post(
    "/company/login",
    response_model=Token,
    summary="Log in as a Company",
)
def login_company(
    db: DB,
    form: OAuth2PasswordRequestForm = Depends(),
):
    company = db.query(Company).filter(Company.ContactEmail == form.username).first()
    if company is None or not verify_password(form.password, company.PasswordHash):
        raise _unauthorized()

    return Token(
        access_token=create_access_token(company.CompanyID, "company"),
        token_type="bearer",
    )


@router.post(
    "/signup",
    response_model=JobSeekerOut,
    status_code=status.HTTP_201_CREATED,
    summary="Sign up as a JobSeeker",
)
def signup_jobseeker(payload: JobSeekerCreate, db: DB):
    return register_jobseeker(payload, db)
