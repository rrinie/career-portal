"""
routers/jobseekers.py
---------------------
All endpoints for the JobSeeker domain, including their CV_Profile sub-resource.

Access rules (enforced via JWT dependency):
  - A JobSeeker can only read and mutate their OWN profile.
  - The authenticated SeekerID is always taken from the JWT — never trusted
    from the request body or URL to prevent horizontal privilege escalation.

Route map:
  GET    /jobseekers/me                → fetch own profile (with CV nested)
  PATCH  /jobseekers/me                → update own basic info
  DELETE /jobseekers/me                → delete own account (cascades in DB)

  GET    /jobseekers/me/cv             → fetch own CV_Profile
  POST   /jobseekers/me/cv             → create CV_Profile (one per seeker)
  PATCH  /jobseekers/me/cv             → update CV_Profile fields
  DELETE /jobseekers/me/cv             → delete CV_Profile row only

  GET    /jobseekers/me/applications   → list own applications (read-only view)
"""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import DB, CurrentSeeker
from app.models.models import CV_Profile, Application
from app.schemas.jobseeker import (
    JobSeekerOut,
    JobSeekerUpdate,
    CV_ProfileCreate,
    CV_ProfileUpdate,
    CV_ProfileOut,
)
from app.schemas.interview import ApplicationOut

router = APIRouter(
    prefix="/jobseekers",
    tags=["JobSeekers"],
)


# ===========================================================================
# JOBSEEKER PROFILE — /jobseekers/me
# ===========================================================================

@router.get(
    "/me",
    response_model=JobSeekerOut,
    summary="Get my profile",
    description="Returns the authenticated JobSeeker's full profile, including their CV if one exists.",
)
def get_my_profile(current_seeker: CurrentSeeker):
    """
    No DB query needed here — `current_seeker` is already the fully loaded
    ORM object from the `get_current_jobseeker` dependency.
    The `cv_profile` relationship is lazy-loaded by SQLAlchemy on access,
    so it is included automatically via the `JobSeekerOut` response model.
    """
    return current_seeker


@router.patch(
    "/me",
    response_model=JobSeekerOut,
    summary="Update my profile",
    description="Update FirstName, LastName, or Phone. Email and password changes are not permitted here.",
)
def update_my_profile(
    payload: JobSeekerUpdate,
    db: DB,
    current_seeker: CurrentSeeker,
):
    """
    Applies only the fields that are explicitly set in the request body.
    Fields left as null/omitted are NOT overwritten (true partial update).
    """
    # model_dump(exclude_unset=True) returns only fields the client actually sent,
    # so a PATCH with {"Phone": "123"} will not wipe out FirstName.
    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No updatable fields were provided.",
        )

    for field, value in update_data.items():
        setattr(current_seeker, field, value)

    db.commit()
    db.refresh(current_seeker)
    return current_seeker


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete my account",
    description=(
        "Permanently deletes the authenticated JobSeeker and all associated data "
        "(CV_Profile, Applications, VideoInterviews) via the ON DELETE CASCADE "
        "rules defined in the database schema."
    ),
)
def delete_my_account(db: DB, current_seeker: CurrentSeeker):
    db.delete(current_seeker)
    db.commit()
    # 204 No Content — return nothing


# ===========================================================================
# CV PROFILE — /jobseekers/me/cv
# ===========================================================================

@router.get(
    "/me/cv",
    response_model=CV_ProfileOut,
    summary="Get my CV profile",
)
def get_my_cv(current_seeker: CurrentSeeker):
    if current_seeker.cv_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No CV profile found. Use POST /jobseekers/me/cv to create one.",
        )
    return current_seeker.cv_profile


@router.post(
    "/me/cv",
    response_model=CV_ProfileOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create my CV profile",
    description=(
        "Creates a CV_Profile for the authenticated seeker. "
        "The schema enforces a UNIQUE constraint on SeekerID — only one CV per seeker."
    ),
)
def create_my_cv(
    payload: CV_ProfileCreate,
    db: DB,
    current_seeker: CurrentSeeker,
):
    # Guard: enforce one-CV-per-seeker at the application layer
    # (the DB UNIQUE constraint is the final safety net)
    if current_seeker.cv_profile is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A CV profile already exists for this account. "
                "Use PATCH /jobseekers/me/cv to update it."
            ),
        )

    cv = CV_Profile(
        SeekerID        = current_seeker.SeekerID,
        EducationLevel  = payload.EducationLevel,
        ExperienceYears = payload.ExperienceYears,
        LinkedInURL     = payload.LinkedInURL,
        Summary         = payload.Summary,
    )
    db.add(cv)
    db.commit()
    db.refresh(cv)
    return cv


@router.patch(
    "/me/cv",
    response_model=CV_ProfileOut,
    summary="Update my CV profile",
    description="Partial update — only the fields you include in the body are changed.",
)
def update_my_cv(
    payload: CV_ProfileUpdate,
    db: DB,
    current_seeker: CurrentSeeker,
):
    if current_seeker.cv_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No CV profile found. Use POST /jobseekers/me/cv to create one first.",
        )

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


@router.delete(
    "/me/cv",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete my CV profile",
    description=(
        "Removes only the CV_Profile row. The JobSeeker account itself is preserved. "
        "ON DELETE CASCADE in the schema handles this automatically."
    ),
)
def delete_my_cv(db: DB, current_seeker: CurrentSeeker):
    if current_seeker.cv_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No CV profile found — nothing to delete.",
        )

    db.delete(current_seeker.cv_profile)
    db.commit()


# ===========================================================================
# APPLICATIONS — /jobseekers/me/applications  (read-only view)
# Full POST logic lives in routers/applications.py
# ===========================================================================

@router.get(
    "/me/applications",
    response_model=list[ApplicationOut],
    summary="List my applications",
    description="Returns all applications submitted by the authenticated JobSeeker, newest first.",
)
def list_my_applications(db: DB, current_seeker: CurrentSeeker):
    applications = (
        db.query(Application)
        .filter(Application.SeekerID == current_seeker.SeekerID)
        .order_by(Application.ApplicationDate.desc())
        .all()
    )
    return applications
