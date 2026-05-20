"""
VideoInterview endpoints for candidate submissions and company review.
"""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import CurrentCompany, CurrentSeeker, DB
from app.models.models import Application, JobPosting, QuestionPackage, VideoInterview
from app.schemas.interview import VideoInterviewCreate, VideoInterviewOut, VideoInterviewReview

router = APIRouter(prefix="/interviews", tags=["Video Interviews"])


@router.post("", response_model=VideoInterviewOut, status_code=status.HTTP_201_CREATED, summary="Submit a video interview")
def submit_interview(payload: VideoInterviewCreate, db: DB, current_seeker: CurrentSeeker):
    application = _get_application_or_404(db, payload.ApplicationID)
    if application.SeekerID != current_seeker.SeekerID:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to submit an interview for this application.")

    package = _get_package_or_404(db, payload.PackageID)
    if package.PostingID != application.PostingID:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="QuestionPackage does not belong to the same posting as the Application.",
        )

    existing = db.query(VideoInterview).filter(
        VideoInterview.ApplicationID == payload.ApplicationID,
        VideoInterview.PackageID == payload.PackageID,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A VideoInterview already exists for this application and package (InterviewID: {existing.InterviewID}).",
        )

    interview = VideoInterview(
        ApplicationID=payload.ApplicationID,
        PackageID=payload.PackageID,
        VideoURL=payload.VideoURL,
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return interview


@router.get("/company/{interview_id}", response_model=VideoInterviewOut, summary="Get a video interview as company")
def get_interview_as_company(interview_id: int, db: DB, current_company: CurrentCompany):
    interview = _get_interview_or_404(db, interview_id)
    _assert_company_owns_interview(db, interview, current_company.CompanyID)
    return interview


@router.get("/application/{application_id}", response_model=list[VideoInterviewOut], summary="List my interviews for an application")
def list_interviews_for_application(application_id: int, db: DB, current_seeker: CurrentSeeker):
    application = _get_application_or_404(db, application_id)
    if application.SeekerID != current_seeker.SeekerID:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to view interviews for this application.")
    return db.query(VideoInterview).filter(VideoInterview.ApplicationID == application_id).all()


@router.get("/{interview_id}", response_model=VideoInterviewOut, summary="Get my video interview")
def get_interview_as_seeker(interview_id: int, db: DB, current_seeker: CurrentSeeker):
    interview = _get_interview_or_404(db, interview_id)
    application = _get_application_or_404(db, interview.ApplicationID)
    if application.SeekerID != current_seeker.SeekerID:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to view this interview.")
    return interview


@router.patch("/{interview_id}/review", response_model=VideoInterviewOut, summary="Review a video interview")
def review_interview(interview_id: int, payload: VideoInterviewReview, db: DB, current_company: CurrentCompany):
    interview = _get_interview_or_404(db, interview_id)
    _assert_company_owns_interview(db, interview, current_company.CompanyID)

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No review fields were provided.")

    for field, value in update_data.items():
        setattr(interview, field, value)

    db.commit()
    db.refresh(interview)
    return interview


@router.delete("/{interview_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete my video interview")
def delete_interview(interview_id: int, db: DB, current_seeker: CurrentSeeker):
    interview = _get_interview_or_404(db, interview_id)
    application = _get_application_or_404(db, interview.ApplicationID)
    if application.SeekerID != current_seeker.SeekerID:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to delete this interview.")

    db.delete(interview)
    db.commit()


def _get_interview_or_404(db: Session, interview_id: int) -> VideoInterview:
    interview = db.query(VideoInterview).filter(VideoInterview.InterviewID == interview_id).first()
    if interview is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"VideoInterview with ID {interview_id} not found.")
    return interview


def _get_application_or_404(db: Session, application_id: int) -> Application:
    application = db.query(Application).filter(Application.ApplicationID == application_id).first()
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Application with ID {application_id} not found.")
    return application


def _get_package_or_404(db: Session, package_id: int) -> QuestionPackage:
    package = db.query(QuestionPackage).filter(QuestionPackage.PackageID == package_id).first()
    if package is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"QuestionPackage with ID {package_id} not found.")
    return package


def _assert_company_owns_interview(db: Session, interview: VideoInterview, company_id: int) -> None:
    application = _get_application_or_404(db, interview.ApplicationID)
    posting = db.query(JobPosting).filter(JobPosting.PostingID == application.PostingID).first()
    if posting is None or posting.CompanyID != company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access this interview.")
