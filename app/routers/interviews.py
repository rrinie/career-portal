"""
routers/interviews.py
---------------------
Handles the VideoInterview lifecycle.

How video submission works in this architecture:
  1. The client uploads a video to an external storage service
     (e.g. AWS S3, Cloudflare R2, Azure Blob).
  2. The client receives a public or pre-signed URL from that service.
  3. The client calls POST /interviews with the VideoURL string.
  4. We store only the URL — no binary data ever touches this API.
     This honours Rule #2 from the architectural spec.

Access rules:
  - POST /interviews                   → JobSeeker JWT.
                                         Must own the Application being linked.
  - GET  /interviews/{id}              → JobSeeker (own) OR Company (their posting).
                                         Implemented as two separate endpoints to
                                         avoid a complex dual-dependency.
  - GET  /interviews/application/{id}  → JobSeeker: see all interviews on one application.
  - PATCH /interviews/{id}/review      → Company JWT only. Adds Score + ReviewerNotes.
  - DELETE /interviews/{id}            → JobSeeker JWT only. Removes own submission.

Route map:
  POST   /interviews                         → Submit video interview
  GET    /interviews/{id}                    → Get one interview (seeker view)
  GET    /interviews/application/{app_id}    → List all interviews on an application
  PATCH  /interviews/{id}/review             → Company scores an interview
  DELETE /interviews/{id}                    → Seeker removes their video submission
"""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import DB, CurrentSeeker, CurrentCompany
from app.models.models import Application, JobPosting, QuestionPackage, VideoInterview
from app.schemas.interview import (
    VideoInterviewCreate,
    VideoInterviewOut,
    VideoInterviewReview,
)

router = APIRouter(prefix="/interviews", tags=["Video Interviews"])


# ===========================================================================
# SUBMIT VIDEO INTERVIEW
# ===========================================================================

@router.post(
    "",
    response_model=VideoInterviewOut,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a video interview",
    description=(
        "JobSeeker-authenticated. Links a hosted VideoURL to an Application + QuestionPackage. "
        "The seeker must own the Application. The QuestionPackage must belong to the same "
        "posting as the Application — this is validated before insertion."
    ),
)
def submit_interview(
    payload: VideoInterviewCreate,
    db: DB,
    current_seeker: CurrentSeeker,
):
    # 1. Verify the application exists and belongs to this seeker
    application = _get_application_or_404(db, payload.ApplicationID)
    if application.SeekerID != current_seeker.SeekerID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to submit an interview for this application.",
        )

    # 2. Verify the package exists
    package = db.query(QuestionPackage).filter(
        QuestionPackage.PackageID == payload.PackageID
    ).first()
    if package is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"QuestionPackage with ID {payload.PackageID} not found.",
        )

    # 3. Cross-resource integrity check:
    #    The package must belong to the same posting as the application.
    #    Without this, a seeker could link any random package to their interview.
    if package.PostingID != application.PostingID:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"QuestionPackage {payload.PackageID} does not belong to the same "
                f"posting as Application {payload.ApplicationID}."
            ),
        )

    # 4. Guard: one video interview per application+package combination
    existing = db.query(VideoInterview).filter(
        VideoInterview.ApplicationID == payload.ApplicationID,
        VideoInterview.PackageID     == payload.PackageID,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A video interview for this application and package already exists "
                f"(InterviewID: {existing.InterviewID}). "
                "Use PATCH /interviews/{id}/review to update it, or DELETE it first."
            ),
        )

    # 5. Create — VideoURL stored as plain string per architectural rule
    interview = VideoInterview(
        ApplicationID = payload.ApplicationID,
        PackageID     = payload.PackageID,
        VideoURL      = payload.VideoURL,   # string URL, never binary
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return interview


# ===========================================================================
# GET ONE INTERVIEW  (JobSeeker view — own interviews only)
# ===========================================================================

@router.get(
    "/{interview_id}",
    response_model=VideoInterviewOut,
    summary="Get a video interview (seeker view)",
    description=(
        "JobSeeker-authenticated. Returns a single VideoInterview. "
        "The seeker may only view interviews linked to their own applications."
    ),
)
def get_interview_as_seeker(
    interview_id: int,
    db: DB,
    current_seeker: CurrentSeeker,
):
    interview = _get_interview_or_404(db, interview_id)

    # Ownership check via the linked application
    application = _get_application_or_404(db, interview.ApplicationID)
    if application.SeekerID != current_seeker.SeekerID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this interview.",
        )

    return interview


# ===========================================================================
# LIST INTERVIEWS ON AN APPLICATION  (JobSeeker — own application only)
# ===========================================================================

@router.get(
    "/application/{application_id}",
    response_model=list[VideoInterviewOut],
    summary="List all video interviews for an application",
    description=(
        "JobSeeker-authenticated. Returns every VideoInterview linked to a single "
        "Application. The seeker must own that application."
    ),
)
def list_interviews_for_application(
    application_id: int,
    db: DB,
    current_seeker: CurrentSeeker,
):
    application = _get_application_or_404(db, application_id)

    if application.SeekerID != current_seeker.SeekerID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view interviews for this application.",
        )

    return (
        db.query(VideoInterview)
        .filter(VideoInterview.ApplicationID == application_id)
        .all()
    )


# ===========================================================================
# REVIEW AN INTERVIEW  (Company only — score + notes)
# ===========================================================================

@router.patch(
    "/{interview_id}/review",
    response_model=VideoInterviewOut,
    summary="Score and review a video interview",
    description=(
        "Company-authenticated. Adds a Score (Decimal 0–999.99) and/or ReviewerNotes "
        "to a VideoInterview. The interview must belong to an application on one of "
        "the authenticated company's job postings. "
        "Both fields are optional — send only the ones you want to set."
    ),
)
def review_interview(
    interview_id: int,
    payload: VideoInterviewReview,
    db: DB,
    current_company: CurrentCompany,
):
    interview = _get_interview_or_404(db, interview_id)

    # Verify the interview links to a posting owned by this company
    application = _get_application_or_404(db, interview.ApplicationID)
    posting = db.query(JobPosting).filter(
        JobPosting.PostingID == application.PostingID
    ).first()

    if posting is None or posting.CompanyID != current_company.CompanyID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to review this interview.",
        )

    # Partial update — only set the fields the reviewer explicitly provided
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No review fields were provided. Supply Score, ReviewerNotes, or both.",
        )

    for field, value in update_data.items():
        setattr(interview, field, value)

    db.commit()
    db.refresh(interview)
    return interview


# ===========================================================================
# DELETE VIDEO INTERVIEW  (JobSeeker only)
# ===========================================================================

@router.delete(
    "/{interview_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a video interview submission",
    description=(
        "JobSeeker-authenticated. Removes a VideoInterview record. "
        "Use this to re-submit after uploading a corrected video to external storage."
    ),
)
def delete_interview(
    interview_id: int,
    db: DB,
    current_seeker: CurrentSeeker,
):
    interview = _get_interview_or_404(db, interview_id)

    application = _get_application_or_404(db, interview.ApplicationID)
    if application.SeekerID != current_seeker.SeekerID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this interview.",
        )

    db.delete(interview)
    db.commit()


# ===========================================================================
# PRIVATE HELPERS
# ===========================================================================

def _get_interview_or_404(db: Session, interview_id: int) -> VideoInterview:
    interview = db.query(VideoInterview).filter(
        VideoInterview.InterviewID == interview_id
    ).first()
    if interview is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VideoInterview with ID {interview_id} not found.",
        )
    return interview


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
