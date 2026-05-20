"""
JobSeeker profile, CV_Profile, and seeker-owned application endpoints.
"""

from fastapi import APIRouter, HTTPException, status

from app.core.security import hash_password
from app.dependencies import CurrentSeeker, DB
from app.models.models import Application, CV_Profile, JobSeeker
from app.schemas.interview import ApplicationOut
from app.schemas.jobseeker import CV_ProfileCreate, CV_ProfileOut, CV_ProfileUpdate, JobSeekerOut, JobSeekerUpdate

router = APIRouter(prefix="/jobseekers", tags=["JobSeekers"])


@router.get("/me", response_model=JobSeekerOut, summary="Get my profile")
def get_my_profile(current_seeker: CurrentSeeker):
    return current_seeker


@router.patch("/me", response_model=JobSeekerOut, summary="Update my profile")
def update_my_profile(payload: JobSeekerUpdate, db: DB, current_seeker: CurrentSeeker):
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No updatable fields were provided.",
        )

    if "Email" in update_data:
        existing = db.query(JobSeeker).filter(
            JobSeeker.Email == update_data["Email"],
            JobSeeker.SeekerID != current_seeker.SeekerID,
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A JobSeeker with this email already exists.",
            )
        update_data["Email"] = str(update_data["Email"])

    if "Password" in update_data:
        current_seeker.PasswordHash = hash_password(update_data.pop("Password"))

    for field, value in update_data.items():
        setattr(current_seeker, field, value)

    db.commit()
    db.refresh(current_seeker)
    return current_seeker


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT, summary="Delete my account")
def delete_my_account(db: DB, current_seeker: CurrentSeeker):
    db.delete(current_seeker)
    db.commit()


@router.get("/me/cv", response_model=CV_ProfileOut, summary="Get my CV profile")
def get_my_cv(current_seeker: CurrentSeeker):
    if current_seeker.cv_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No CV profile found.")
    return current_seeker.cv_profile


@router.post("/me/cv", response_model=CV_ProfileOut, status_code=status.HTTP_201_CREATED, summary="Create my CV profile")
def create_my_cv(payload: CV_ProfileCreate, db: DB, current_seeker: CurrentSeeker):
    if current_seeker.cv_profile is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A CV profile already exists for this account.",
        )

    cv = CV_Profile(
        SeekerID=current_seeker.SeekerID,
        EducationLevel=payload.EducationLevel,
        ExperienceYears=payload.ExperienceYears,
        LinkedInURL=payload.LinkedInURL,
        Summary=payload.Summary,
    )
    db.add(cv)
    db.commit()
    db.refresh(cv)
    return cv


@router.patch("/me/cv", response_model=CV_ProfileOut, summary="Update my CV profile")
def update_my_cv(payload: CV_ProfileUpdate, db: DB, current_seeker: CurrentSeeker):
    if current_seeker.cv_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No CV profile found.")

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No updatable fields were provided.",
        )

    for field, value in update_data.items():
        setattr(current_seeker.cv_profile, field, value)

    db.commit()
    db.refresh(current_seeker.cv_profile)
    return current_seeker.cv_profile


@router.delete("/me/cv", status_code=status.HTTP_204_NO_CONTENT, summary="Delete my CV profile")
def delete_my_cv(db: DB, current_seeker: CurrentSeeker):
    if current_seeker.cv_profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No CV profile found.")

    db.delete(current_seeker.cv_profile)
    db.commit()


@router.get("/me/applications", response_model=list[ApplicationOut], summary="List my applications")
def list_my_applications(db: DB, current_seeker: CurrentSeeker):
    return (
        db.query(Application)
        .filter(Application.SeekerID == current_seeker.SeekerID)
        .order_by(Application.ApplicationDate.desc())
        .all()
    )
