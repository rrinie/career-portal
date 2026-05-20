"""
Company profile and company-owned JobPosting endpoints.
"""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.dependencies import CurrentCompany, DB
from app.models.models import Application, Company, JobPosting, Position
from app.schemas.company import CompanyOut, CompanyUpdate
from app.schemas.interview import ApplicationOut
from app.schemas.job import JobPostingCreate, JobPostingOut, JobPostingUpdate

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.get("/me", response_model=CompanyOut, summary="Get my company profile")
def get_my_company(current_company: CurrentCompany):
    return current_company


@router.patch("/me", response_model=CompanyOut, summary="Update my company profile")
def update_my_company(payload: CompanyUpdate, db: DB, current_company: CurrentCompany):
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No updatable fields were provided.",
        )

    if "ContactEmail" in update_data:
        existing = db.query(Company).filter(
            Company.ContactEmail == update_data["ContactEmail"],
            Company.CompanyID != current_company.CompanyID,
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A Company with this contact email already exists.",
            )
        update_data["ContactEmail"] = str(update_data["ContactEmail"])

    if "Password" in update_data:
        current_company.PasswordHash = hash_password(update_data.pop("Password"))

    for field, value in update_data.items():
        setattr(current_company, field, value)

    db.commit()
    db.refresh(current_company)
    return current_company


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT, summary="Delete my company account")
def delete_my_company(db: DB, current_company: CurrentCompany):
    db.delete(current_company)
    db.commit()


@router.get("/me/postings", response_model=list[JobPostingOut], summary="List my job postings")
def list_my_postings(db: DB, current_company: CurrentCompany):
    return (
        db.query(JobPosting)
        .filter(JobPosting.CompanyID == current_company.CompanyID)
        .order_by(JobPosting.PostingID.desc())
        .all()
    )


@router.post(
    "/me/postings",
    response_model=JobPostingOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a job posting",
)
def create_posting(payload: JobPostingCreate, db: DB, current_company: CurrentCompany):
    _get_position_or_404(db, payload.PositionID)

    posting = JobPosting(
        CompanyID=current_company.CompanyID,
        PositionID=payload.PositionID,
        Title=payload.Title,
        WorkType=payload.WorkType,
        Deadline=payload.Deadline,
    )
    db.add(posting)
    db.commit()
    db.refresh(posting)
    return posting


@router.get("/me/postings/{posting_id}", response_model=JobPostingOut, summary="Get my job posting")
def get_my_posting(posting_id: int, db: DB, current_company: CurrentCompany):
    return _get_owned_posting(db, posting_id, current_company.CompanyID)


@router.patch("/me/postings/{posting_id}", response_model=JobPostingOut, summary="Update my job posting")
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

    if "PositionID" in update_data:
        _get_position_or_404(db, update_data["PositionID"])

    for field, value in update_data.items():
        setattr(posting, field, value)

    db.commit()
    db.refresh(posting)
    return posting


@router.delete("/me/postings/{posting_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete my job posting")
def delete_my_posting(posting_id: int, db: DB, current_company: CurrentCompany):
    posting = _get_owned_posting(db, posting_id, current_company.CompanyID)
    db.delete(posting)
    db.commit()


@router.get(
    "/me/postings/{posting_id}/applications",
    response_model=list[ApplicationOut],
    summary="List applications for my job posting",
)
def list_posting_applications(posting_id: int, db: DB, current_company: CurrentCompany):
    _get_owned_posting(db, posting_id, current_company.CompanyID)
    return (
        db.query(Application)
        .filter(Application.PostingID == posting_id)
        .order_by(Application.ApplicationDate.desc())
        .all()
    )


def _get_position_or_404(db: Session, position_id: int) -> Position:
    position = db.query(Position).filter(Position.PositionID == position_id).first()
    if position is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Position with ID {position_id} not found.",
        )
    return position


def _get_owned_posting(db: Session, posting_id: int, company_id: int) -> JobPosting:
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
