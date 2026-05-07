"""
routers/companies.py
--------------------
All endpoints for the Company domain, including their JobPostings sub-resource.

Access rules (enforced via JWT dependency):
  - A Company can only mutate its OWN profile and job postings.
  - CompanyID is always taken from the JWT — never from the URL or body —
    to prevent horizontal privilege escalation.
  - Any authenticated actor (JobSeeker or anonymous) can view company
    profiles and listings via the public read endpoints.

Route map:
  GET    /companies/me                       → fetch own company profile
  PATCH  /companies/me                       → update own company info
  DELETE /companies/me                       → delete account + all postings (CASCADE)

  GET    /companies/me/postings              → list own job postings
  POST   /companies/me/postings              → create a new job posting
  GET    /companies/me/postings/{posting_id} → get one of own postings (with packages)
  PATCH  /companies/me/postings/{posting_id} → update own posting
  DELETE /companies/me/postings/{posting_id} → delete own posting + packages + apps (CASCADE)

  GET    /companies/me/postings/{posting_id}/applications
                                             → list all applications for a posting
                                               (company reviews these)
"""

from fastapi import APIRouter, HTTPException, status

from app.dependencies import DB, CurrentCompany
from app.models.models import JobPosting, Application
from app.schemas.company import CompanyOut, CompanyUpdate
from app.schemas.job import JobPostingCreate, JobPostingUpdate, JobPostingOut
from app.schemas.interview import ApplicationOut

router = APIRouter(
    prefix="/companies",
    tags=["Companies"],
)


# ===========================================================================
# COMPANY PROFILE — /companies/me
# ===========================================================================

@router.get(
    "/me",
    response_model=CompanyOut,
    summary="Get my company profile",
)
def get_my_company(current_company: CurrentCompany):
    """
    Returns the authenticated Company's profile.
    The ORM object from the dependency is returned directly.
    """
    return current_company


@router.patch(
    "/me",
    response_model=CompanyOut,
    summary="Update my company profile",
    description=(
        "Update CompanyName, Industry, or City. "
        "ContactEmail changes are not permitted here to avoid auth confusion."
    ),
)
def update_my_company(
    payload: CompanyUpdate,
    db: DB,
    current_company: CurrentCompany,
):
    """
    Partial update — only fields present in the request body are written.
    Fields omitted from the body are left unchanged.
    """
    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No updatable fields were provided.",
        )

    for field, value in update_data.items():
        setattr(current_company, field, value)

    db.commit()
    db.refresh(current_company)
    return current_company


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete my company account",
    description=(
        "Permanently deletes the authenticated Company. "
        "All associated JobPostings, QuestionPackages, and Applications "
        "are removed automatically via ON DELETE CASCADE."
    ),
)
def delete_my_company(db: DB, current_company: CurrentCompany):
    db.delete(current_company)
    db.commit()


# ===========================================================================
# JOB POSTINGS — /companies/me/postings
# ===========================================================================

@router.get(
    "/me/postings",
    response_model=list[JobPostingOut],
    summary="List my job postings",
    description="Returns all JobPostings belonging to the authenticated Company.",
)
def list_my_postings(db: DB, current_company: CurrentCompany):
    postings = (
        db.query(JobPosting)
        .filter(JobPosting.CompanyID == current_company.CompanyID)
        .order_by(JobPosting.PostingID.desc())
        .all()
    )
    return postings


@router.post(
    "/me/postings",
    response_model=JobPostingOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a job posting",
    description=(
        "Creates a new JobPosting owned by the authenticated Company. "
        "The CompanyID is injected from the JWT — it cannot be spoofed via the request body."
    ),
)
def create_posting(
    payload: JobPostingCreate,
    db: DB,
    current_company: CurrentCompany,
):
    """
    Note: `payload.CompanyID` from the schema is intentionally IGNORED here.
    The CompanyID is always sourced from `current_company.CompanyID` (the JWT)
    so a logged-in company cannot create postings on behalf of another company.
    """
    posting = JobPosting(
        CompanyID  = current_company.CompanyID,   # always from JWT
        PositionID = payload.PositionID,
        Title      = payload.Title,
        WorkType   = payload.WorkType,
        Deadline   = payload.Deadline,
    )
    db.add(posting)
    db.commit()
    db.refresh(posting)
    return posting


@router.get(
    "/me/postings/{posting_id}",
    response_model=JobPostingOut,
    summary="Get one of my job postings",
    description="Returns a single JobPosting with its nested QuestionPackages and Questions.",
)
def get_my_posting(
    posting_id: int,
    db: DB,
    current_company: CurrentCompany,
):
    posting = _get_owned_posting(db, posting_id, current_company.CompanyID)
    return posting


@router.patch(
    "/me/postings/{posting_id}",
    response_model=JobPostingOut,
    summary="Update one of my job postings",
    description="Partial update on Title, WorkType, or Deadline. Only supplied fields are changed.",
)
def update_my_posting(
    posting_id: int,
    payload: JobPostingUpdate,
    db: DB,
    current_company: CurrentCompany,
):
    posting = _get_owned_posting(db, posting_id, current_company.CompanyID)

    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No updatable fields were provided.",
        )

    for field, value in update_data.items():
        setattr(posting, field, value)

    db.commit()
    db.refresh(posting)
    return posting


@router.delete(
    "/me/postings/{posting_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete one of my job postings",
    description=(
        "Permanently removes a JobPosting. All linked QuestionPackages, Questions, "
        "Applications, and VideoInterviews are removed via ON DELETE CASCADE."
    ),
)
def delete_my_posting(
    posting_id: int,
    db: DB,
    current_company: CurrentCompany,
):
    posting = _get_owned_posting(db, posting_id, current_company.CompanyID)
    db.delete(posting)
    db.commit()


# ===========================================================================
# APPLICATIONS PER POSTING — /companies/me/postings/{posting_id}/applications
# ===========================================================================

@router.get(
    "/me/postings/{posting_id}/applications",
    response_model=list[ApplicationOut],
    summary="List applications for a job posting",
    description=(
        "Returns all Applications submitted for one of the authenticated Company's postings. "
        "The company can use this to review candidates. "
        "Status updates are handled via PATCH /applications/{application_id}/status."
    ),
)
def list_posting_applications(
    posting_id: int,
    db: DB,
    current_company: CurrentCompany,
):
    # Verify the posting belongs to this company before exposing applicant data
    _get_owned_posting(db, posting_id, current_company.CompanyID)

    applications = (
        db.query(Application)
        .filter(Application.PostingID == posting_id)
        .order_by(Application.ApplicationDate.desc())
        .all()
    )
    return applications


# ===========================================================================
# PRIVATE HELPER
# ===========================================================================

def _get_owned_posting(db, posting_id: int, company_id: int) -> JobPosting:
    """
    Fetch a JobPosting by ID and verify it belongs to the requesting Company.

    Returns the posting on success.
    Raises 404 if the posting doesn't exist.
    Raises 403 if the posting exists but belongs to a different company.

    This two-step error strategy is intentional:
      - 404 when the resource simply doesn't exist (no information leak).
      - 403 when the resource exists but the caller doesn't own it
        (tells the developer they hit the wrong endpoint, not a missing resource).
    """
    posting = db.query(JobPosting).filter(JobPosting.PostingID == posting_id).first()

    if posting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"JobPosting with ID {posting_id} not found.",
        )

    if posting.CompanyID != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this job posting.",
        )

    return posting
