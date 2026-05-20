"""
Application endpoints backed by the normalized Application junction table.
"""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import CurrentCompany, CurrentSeeker, DB
from app.models.models import Application, JobPosting
from app.schemas.interview import ApplicationCreate, ApplicationOut, ApplicationStatusUpdate

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post("", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED, summary="Submit an application")
def submit_application(payload: ApplicationCreate, db: DB, current_seeker: CurrentSeeker):
    _get_posting_or_404(db, payload.PostingID)

    existing = db.query(Application).filter(
        Application.SeekerID == current_seeker.SeekerID,
        Application.PostingID == payload.PostingID,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"You have already applied for this posting (ApplicationID: {existing.ApplicationID}).",
        )

    application = Application(
        SeekerID=current_seeker.SeekerID,
        PostingID=payload.PostingID,
        Status="Pending",
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@router.get("/{application_id}", response_model=ApplicationOut, summary="Get my application")
def get_application(application_id: int, db: DB, current_seeker: CurrentSeeker):
    application = _get_application_or_404(db, application_id)
    if application.SeekerID != current_seeker.SeekerID:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to view this application.")
    return application


@router.patch("/{application_id}/status", response_model=ApplicationOut, summary="Update application status")
def update_application_status(
    application_id: int,
    payload: ApplicationStatusUpdate,
    db: DB,
    current_company: CurrentCompany,
):
    application = _get_application_or_404(db, application_id)
    posting = _get_posting_or_404(db, application.PostingID)
    if posting.CompanyID != current_company.CompanyID:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to update this application.")

    application.Status = payload.Status
    db.commit()
    db.refresh(application)
    return application


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Withdraw my application")
def withdraw_application(application_id: int, db: DB, current_seeker: CurrentSeeker):
    application = _get_application_or_404(db, application_id)
    if application.SeekerID != current_seeker.SeekerID:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to withdraw this application.")

    db.delete(application)
    db.commit()


def _get_application_or_404(db: Session, application_id: int) -> Application:
    application = db.query(Application).filter(Application.ApplicationID == application_id).first()
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Application with ID {application_id} not found.")
    return application


def _get_posting_or_404(db: Session, posting_id: int) -> JobPosting:
    posting = db.query(JobPosting).filter(JobPosting.PostingID == posting_id).first()
    if posting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"JobPosting with ID {posting_id} not found.")
    return posting
