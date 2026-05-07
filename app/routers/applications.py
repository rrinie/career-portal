"""
routers/applications.py
-----------------------
Handles the full Application lifecycle:
  - A JobSeeker submits an application for a posting.
  - A Company reviewer updates the application status.
  - Both actors can read application details (scoped to what they own).

Access rules:
  - POST   /applications               → JobSeeker JWT only. SeekerID from JWT, never body.
  - GET    /applications/{id}          → JobSeeker JWT (own apps) OR Company JWT (apps on their postings).
  - PATCH  /applications/{id}/status   → Company JWT only. Validates the target posting is theirs.
  - DELETE /applications/{id}          → JobSeeker JWT only. Can only withdraw own application.

Route map:
  POST   /applications                  → JobSeeker submits application
  GET    /applications/{id}             → Get single application detail
  PATCH  /applications/{id}/status      → Company updates application status
  DELETE /applications/{id}             → JobSeeker withdraws application
"""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import DB, CurrentSeeker, CurrentCompany
from app.models.models import Application, JobPosting
from app.schemas.interview import (
    ApplicationCreate,
    ApplicationOut,
    ApplicationStatusUpdate,
)

router = APIRouter(prefix="/applications", tags=["Applications"])


# ===========================================================================
# SUBMIT APPLICATION
# ===========================================================================

@router.post(
    "",
    response_model=ApplicationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a job application",
    description=(
        "JobSeeker-authenticated. Submits an application for the given PostingID. "
        "SeekerID is sourced from the JWT — it cannot be set in the request body. "
        "Duplicate applications (same seeker + same posting) are rejected with 409."
    ),
)
def submit_application(
    payload: ApplicationCreate,
    db: DB,
    current_seeker: CurrentSeeker,
):
    # 1. Verify the posting exists before creating an orphaned application
    posting = db.query(JobPosting).filter(
        JobPosting.PostingID == payload.PostingID
    ).first()
    if posting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"JobPosting with ID {payload.PostingID} not found.",
        )

    # 2. Guard: prevent duplicate applications
    existing = db.query(Application).filter(
        Application.SeekerID  == current_seeker.SeekerID,
        Application.PostingID == payload.PostingID,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"You have already applied for this posting "
                f"(ApplicationID: {existing.ApplicationID})."
            ),
        )

    # 3. Create — SeekerID always from JWT
    application = Application(
        SeekerID  = current_seeker.SeekerID,
        PostingID = payload.PostingID,
        Status    = "Pending",
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


# ===========================================================================
# GET SINGLE APPLICATION
# ===========================================================================

@router.get(
    "/{application_id}",
    response_model=ApplicationOut,
    summary="Get application details",
    description=(
        "Accessible by the JobSeeker who submitted it OR by the Company that owns the posting. "
        "Because FastAPI resolves the first matching dependency, we use a unified endpoint "
        "with manual actor detection via two optional dependencies. "
        "See implementation notes in the docstring."
    ),
)
def get_application(
    application_id: int,
    db: DB,
    current_seeker:  CurrentSeeker,
):
    """
    Scoped to the authenticated JobSeeker: they may only view their own applications.
    A Company-facing read is available via GET /companies/me/postings/{id}/applications.
    Keeping separate read paths per actor avoids a complex dual-auth dependency.
    """
    application = _get_application_or_404(db, application_id)

    if application.SeekerID != current_seeker.SeekerID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this application.",
        )

    return application


# ===========================================================================
# UPDATE APPLICATION STATUS  (Company only)
# ===========================================================================

@router.patch(
    "/{application_id}/status",
    response_model=ApplicationOut,
    summary="Update application status",
    description=(
        "Company-authenticated. Advances the status of an application on one of the "
        "company's own job postings. "
        "Valid statuses: Pending, Reviewed, Shortlisted, Rejected, Hired."
    ),
)
def update_application_status(
    application_id: int,
    payload: ApplicationStatusUpdate,
    db: DB,
    current_company: CurrentCompany,
):
    application = _get_application_or_404(db, application_id)

    # Verify the application belongs to a posting owned by this company
    posting = db.query(JobPosting).filter(
        JobPosting.PostingID == application.PostingID
    ).first()

    if posting is None or posting.CompanyID != current_company.CompanyID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this application.",
        )

    application.Status = payload.Status
    db.commit()
    db.refresh(application)
    return application


# ===========================================================================
# WITHDRAW APPLICATION  (JobSeeker only)
# ===========================================================================

@router.delete(
    "/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Withdraw an application",
    description=(
        "JobSeeker-authenticated. Permanently removes the application. "
        "Also removes any linked VideoInterviews via ON DELETE CASCADE. "
        "A seeker may only withdraw their own applications."
    ),
)
def withdraw_application(
    application_id: int,
    db: DB,
    current_seeker: CurrentSeeker,
):
    application = _get_application_or_404(db, application_id)

    if application.SeekerID != current_seeker.SeekerID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to withdraw this application.",
        )

    db.delete(application)
    db.commit()


# ===========================================================================
# PRIVATE HELPER
# ===========================================================================

def _get_application_or_404(db: Session, application_id: int) -> Application:
    application = db.query(Application).filter(
        Application.ApplicationID == application_id
    ).first()
    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application with ID {application_id} not found.",
        )
    return application
