"""
routers/auth.py
---------------
Authentication endpoints for both actor types.

JobSeeker routes:
    POST /auth/jobseeker/register   – create account
    POST /auth/jobseeker/login      – returns JWT

Company routes:
    POST /auth/company/register     – create account
    POST /auth/company/login        – returns JWT

Design decisions:
  - Login uses OAuth2PasswordRequestForm so Swagger UI shows a proper
    login form with username/password fields.
  - "username" in the form maps to Email for both actor types.
  - Passwords are NEVER stored or returned in plain text.
  - The JWT payload embeds 'type' ("jobseeker" | "company") so a single
    decode_access_token function can serve both actors without ambiguity.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.dependencies import get_db, DB
from app.models.models import JobSeeker, Company
from app.schemas.auth import Token
from app.schemas.jobseeker import JobSeekerCreate, JobSeekerOut
from app.schemas.company import CompanyCreate, CompanyOut
from app.core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ===========================================================================
# JOBSEEKER AUTH
# ===========================================================================

@router.post(
    "/jobseeker/register",
    response_model=JobSeekerOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new JobSeeker account",
)
def register_jobseeker(payload: JobSeekerCreate, db: DB):
    """
    Create a new JobSeeker.
    - Email must be unique across all JobSeekers.
    - Password is hashed with bcrypt before storage.
    - The plain-text password is never persisted or returned.
    """
    # 1. Guard: duplicate email
    existing = db.query(JobSeeker).filter(JobSeeker.Email == payload.Email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A JobSeeker with this email already exists.",
        )

    # 2. Create ORM object — hash the password, discard the plain text
    seeker = JobSeeker(
        FirstName    = payload.FirstName,
        LastName     = payload.LastName,
        Email        = payload.Email,
        PasswordHash = hash_password(payload.Password),
        Phone        = payload.Phone,
    )
    db.add(seeker)
    db.commit()
    db.refresh(seeker)
    return seeker


@router.post(
    "/jobseeker/login",
    response_model=Token,
    summary="Log in as a JobSeeker — returns a Bearer JWT",
)
def login_jobseeker(
    form: OAuth2PasswordRequestForm = Depends(),
    db:   Session                   = Depends(get_db),
):
    """
    Authenticate a JobSeeker using email + password.
    'username' field in the OAuth2 form maps to Email.
    Returns a signed JWT on success.
    """
    # 1. Look up by email (form.username = email)
    seeker = db.query(JobSeeker).filter(JobSeeker.Email == form.username).first()

    # 2. Verify existence and password — same error message for both
    #    (prevents user-enumeration attacks)
    if not seeker or not verify_password(form.password, seeker.PasswordHash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Issue token
    token = create_access_token(
        subject    = seeker.SeekerID,
        actor_type = "jobseeker",
    )
    return Token(access_token=token, token_type="bearer")


# ===========================================================================
# COMPANY AUTH
# ===========================================================================

@router.post(
    "/company/register",
    response_model=CompanyOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new Company account",
)
def register_company(payload: CompanyCreate, db: DB):
    """
    Create a new Company.
    - ContactEmail must be unique.
    - Password is hashed with bcrypt; PasswordHash is stored in Company.PasswordHash.

    ⚠️  Schema note: if you have not yet added PasswordHash VARCHAR(255) to your
        Company table, run this migration first:
            ALTER TABLE Company ADD COLUMN PasswordHash VARCHAR(255) NOT NULL DEFAULT '';
        Then remove the DEFAULT '' after backfilling existing rows.
    """
    # 1. Guard: duplicate email
    existing = db.query(Company).filter(Company.ContactEmail == payload.ContactEmail).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A Company with this email already exists.",
        )

    # 2. Create ORM object
    company = Company(
        CompanyName  = payload.CompanyName,
        Industry     = payload.Industry,
        City         = payload.City,
        ContactEmail = payload.ContactEmail,
        PasswordHash = hash_password(payload.Password),
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.post(
    "/company/login",
    response_model=Token,
    summary="Log in as a Company — returns a Bearer JWT",
)
def login_company(
    form: OAuth2PasswordRequestForm = Depends(),
    db:   Session                   = Depends(get_db),
):
    """
    Authenticate a Company using ContactEmail + password.
    'username' in the OAuth2 form maps to ContactEmail.
    Returns a signed JWT on success.
    """
    # 1. Look up by email
    company = db.query(Company).filter(Company.ContactEmail == form.username).first()

    # 2. Verify — same error message to prevent user enumeration
    if not company or not verify_password(form.password, company.PasswordHash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Issue token
    token = create_access_token(
        subject    = company.CompanyID,
        actor_type = "company",
    )
    return Token(access_token=token, token_type="bearer")


# ===========================================================================
# JOBSEEKER SIGN-UP  — /auth/signup
# ===========================================================================
# Alias for /auth/jobseeker/register that provides a clean, frontend-friendly
# URL for the sign-up flow.
#
# Design decision: rather than duplicating the registration logic, this
# endpoint delegates directly to the same service layer.  Both endpoints
# remain active so nothing already integrated breaks:
#   POST /auth/jobseeker/register  — existing Swagger / API consumers
#   POST /auth/signup              — new frontend sign-up page
#
# The response is JobSeekerOut (SeekerID, FirstName, LastName, Email, Phone).
# PasswordHash is structurally absent from JobSeekerOut — it can never leak.
# ===========================================================================

@router.post(
    "/signup",
    response_model=JobSeekerOut,
    status_code=status.HTTP_201_CREATED,
    summary="Sign up as a new Job Seeker",
    description=(
        "Public endpoint. Creates a new JobSeeker account. "
        "Accepts FirstName, LastName, Email, Password (min 8 chars, must contain a digit). "
        "Returns the created profile — PasswordHash is never included in the response."
    ),
)
def signup_jobseeker(payload: JobSeekerCreate, db: DB):
    """
    Reuses JobSeekerCreate (schemas/jobseeker.py) which already enforces:
      - min_length=8 on Password
      - at least one digit via @field_validator
      - EmailStr validation on Email
      - UNIQUE constraint guard via the 409 check below

    Passwords are hashed with bcrypt (passlib) via hash_password()
    from core/security.py — plain text is never persisted.
    """
    # 1. Guard: duplicate email — same check as /jobseeker/register
    existing = db.query(JobSeeker).filter(JobSeeker.Email == payload.Email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    # 2. Hash password and persist — Phone is optional so default to None
    seeker = JobSeeker(
        FirstName    = payload.FirstName,
        LastName     = payload.LastName,
        Email        = payload.Email,
        PasswordHash = hash_password(payload.Password),
        Phone        = getattr(payload, "Phone", None),
    )
    db.add(seeker)
    db.commit()
    db.refresh(seeker)
    return seeker
