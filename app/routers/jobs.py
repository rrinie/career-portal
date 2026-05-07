"""
routers/jobs.py
---------------
Two distinct responsibilities live here:

  1. PUBLIC JOB BOARD  (no auth required)
     Browse departments, positions, and open job postings.
     Any visitor — logged-in or not — can read these.

  2. QUESTION PACKAGE & QUESTION MANAGEMENT  (Company JWT required)
     A Company manages the interview questions attached to its own postings.
     All write operations verify posting ownership before proceeding.

Route map:

  Public — Departments & Positions:
    GET  /jobs/departments                                   → list all departments
    POST /jobs/departments                                   → create department  [company]
    GET  /jobs/departments/{dept_id}/positions               → list positions in a dept
    POST /jobs/departments/{dept_id}/positions               → create position    [company]

  Public — Job Board:
    GET  /jobs/postings                                      → list all open postings
    GET  /jobs/postings/{posting_id}                         → single posting detail

  Company — Question Packages (owned postings only):
    POST   /jobs/postings/{posting_id}/packages              → create package
    GET    /jobs/postings/{posting_id}/packages/{pkg_id}     → get package + questions
    PATCH  /jobs/postings/{posting_id}/packages/{pkg_id}     → update package meta
    DELETE /jobs/postings/{posting_id}/packages/{pkg_id}     → delete package + questions

  Company — Questions (inside owned packages only):
    POST   /jobs/postings/{posting_id}/packages/{pkg_id}/questions              → add question
    PATCH  /jobs/postings/{posting_id}/packages/{pkg_id}/questions/{q_id}       → update question
    DELETE /jobs/postings/{posting_id}/packages/{pkg_id}/questions/{q_id}       → delete question
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies import DB, CurrentCompany
from app.models.models import Department, Position, JobPosting, QuestionPackage, Question
from app.schemas.job import (
    DepartmentCreate, DepartmentOut,
    PositionCreate,   PositionOut,
    JobPostingOut,
    QuestionPackageCreate, QuestionPackageUpdate, QuestionPackageOut,
    QuestionCreate,   QuestionUpdate,   QuestionOut,
)

router = APIRouter(prefix="/jobs", tags=["Job Board"])


# ===========================================================================
# DEPARTMENTS  — /jobs/departments
# ===========================================================================

@router.get(
    "/departments",
    response_model=list[DepartmentOut],
    summary="List all departments",
    description="Public endpoint. Returns all departments in the system.",
)
def list_departments(db: DB):
    return db.query(Department).order_by(Department.DepartmentName).all()


@router.post(
    "/departments",
    response_model=DepartmentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a department",
    description="Company-authenticated. Adds a new department to the system.",
)
def create_department(
    payload: DepartmentCreate,
    db: DB,
    _: CurrentCompany,              # auth check only — any company can create
):
    dept = Department(DepartmentName=payload.DepartmentName)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


# ===========================================================================
# POSITIONS  — /jobs/departments/{dept_id}/positions
# ===========================================================================

@router.get(
    "/departments/{dept_id}/positions",
    response_model=list[PositionOut],
    summary="List positions in a department",
    description="Public endpoint. Returns all positions belonging to the given department.",
)
def list_positions(dept_id: int, db: DB):
    _get_department_or_404(db, dept_id)
    return (
        db.query(Position)
        .filter(Position.DepartmentID == dept_id)
        .order_by(Position.PositionName)
        .all()
    )


@router.post(
    "/departments/{dept_id}/positions",
    response_model=PositionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a position in a department",
    description="Company-authenticated. The DepartmentID is taken from the URL path, not the body.",
)
def create_position(
    dept_id: int,
    payload: PositionCreate,
    db: DB,
    _: CurrentCompany,
):
    _get_department_or_404(db, dept_id)

    position = Position(
        DepartmentID = dept_id,         # sourced from URL — body value ignored
        PositionName = payload.PositionName,
    )
    db.add(position)
    db.commit()
    db.refresh(position)
    return position


# ===========================================================================
# PUBLIC JOB BOARD  — /jobs/postings
# ===========================================================================

@router.get(
    "/postings",
    response_model=list[JobPostingOut],
    summary="Browse all job postings",
    description=(
        "Public endpoint. Returns all job postings. "
        "Optional query filters: `work_type` (e.g. Remote) and `position_id`."
    ),
)
def list_postings(
    db: DB,
    work_type:   Optional[str] = Query(None, description="Filter by WorkType (Remote / Hybrid / On-site)"),
    position_id: Optional[int] = Query(None, description="Filter by PositionID"),
):
    """
    Supports two optional query-string filters so the frontend can drive a
    filtered job board without needing a separate search endpoint:
        GET /jobs/postings?work_type=Remote
        GET /jobs/postings?position_id=3
        GET /jobs/postings?work_type=Hybrid&position_id=5
    """
    query = db.query(JobPosting)

    if work_type:
        query = query.filter(JobPosting.WorkType == work_type)
    if position_id:
        query = query.filter(JobPosting.PositionID == position_id)

    return query.order_by(JobPosting.PostingID.desc()).all()


@router.get(
    "/postings/{posting_id}",
    response_model=JobPostingOut,
    summary="Get a single job posting",
    description=(
        "Public endpoint. Returns one JobPosting with all its nested "
        "QuestionPackages and Questions — so a candidate can review the "
        "interview format before applying."
    ),
)
def get_posting(posting_id: int, db: DB):
    return _get_posting_or_404(db, posting_id)


# ===========================================================================
# QUESTION PACKAGES  — /jobs/postings/{posting_id}/packages
# All write operations require Company JWT + ownership of the posting.
# ===========================================================================

@router.post(
    "/postings/{posting_id}/packages",
    response_model=QuestionPackageOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a question package for a posting",
    description=(
        "Company-authenticated. Creates a QuestionPackage attached to one of the "
        "authenticated company's own postings."
    ),
)
def create_package(
    posting_id: int,
    payload: QuestionPackageCreate,
    db: DB,
    current_company: CurrentCompany,
):
    _assert_company_owns_posting(db, posting_id, current_company.CompanyID)

    package = QuestionPackage(
        PostingID        = posting_id,      # from URL — payload.PostingID ignored
        PackageName      = payload.PackageName,
        TimeLimitMinutes = payload.TimeLimitMinutes,
    )
    db.add(package)
    db.commit()
    db.refresh(package)
    return package


@router.get(
    "/postings/{posting_id}/packages/{pkg_id}",
    response_model=QuestionPackageOut,
    summary="Get a question package with its questions",
    description="Company-authenticated. Returns a single package and all nested questions.",
)
def get_package(
    posting_id: int,
    pkg_id: int,
    db: DB,
    current_company: CurrentCompany,
):
    _assert_company_owns_posting(db, posting_id, current_company.CompanyID)
    return _get_package_or_404(db, pkg_id, posting_id)


@router.patch(
    "/postings/{posting_id}/packages/{pkg_id}",
    response_model=QuestionPackageOut,
    summary="Update a question package",
    description="Company-authenticated. Partial update on PackageName or TimeLimitMinutes.",
)
def update_package(
    posting_id: int,
    pkg_id: int,
    payload: QuestionPackageUpdate,
    db: DB,
    current_company: CurrentCompany,
):
    _assert_company_owns_posting(db, posting_id, current_company.CompanyID)
    package = _get_package_or_404(db, pkg_id, posting_id)

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No updatable fields were provided.",
        )

    for field, value in update_data.items():
        setattr(package, field, value)

    db.commit()
    db.refresh(package)
    return package


@router.delete(
    "/postings/{posting_id}/packages/{pkg_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a question package",
    description=(
        "Company-authenticated. Removes the package and all its Questions "
        "via ON DELETE CASCADE."
    ),
)
def delete_package(
    posting_id: int,
    pkg_id: int,
    db: DB,
    current_company: CurrentCompany,
):
    _assert_company_owns_posting(db, posting_id, current_company.CompanyID)
    package = _get_package_or_404(db, pkg_id, posting_id)
    db.delete(package)
    db.commit()


# ===========================================================================
# QUESTIONS  — /jobs/postings/{posting_id}/packages/{pkg_id}/questions
# ===========================================================================

@router.post(
    "/postings/{posting_id}/packages/{pkg_id}/questions",
    response_model=QuestionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add a question to a package",
    description="Company-authenticated. Adds one interview question to the specified package.",
)
def create_question(
    posting_id: int,
    pkg_id: int,
    payload: QuestionCreate,
    db: DB,
    current_company: CurrentCompany,
):
    _assert_company_owns_posting(db, posting_id, current_company.CompanyID)
    _get_package_or_404(db, pkg_id, posting_id)    # ensure package belongs to this posting

    question = Question(
        PackageID    = pkg_id,
        QuestionText = payload.QuestionText,
        Points       = payload.Points,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


@router.patch(
    "/postings/{posting_id}/packages/{pkg_id}/questions/{question_id}",
    response_model=QuestionOut,
    summary="Update a question",
    description="Company-authenticated. Partial update on QuestionText or Points.",
)
def update_question(
    posting_id: int,
    pkg_id: int,
    question_id: int,
    payload: QuestionUpdate,
    db: DB,
    current_company: CurrentCompany,
):
    _assert_company_owns_posting(db, posting_id, current_company.CompanyID)
    _get_package_or_404(db, pkg_id, posting_id)
    question = _get_question_or_404(db, question_id, pkg_id)

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No updatable fields were provided.",
        )

    for field, value in update_data.items():
        setattr(question, field, value)

    db.commit()
    db.refresh(question)
    return question


@router.delete(
    "/postings/{posting_id}/packages/{pkg_id}/questions/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a question",
    description="Company-authenticated. Removes a single question from a package.",
)
def delete_question(
    posting_id: int,
    pkg_id: int,
    question_id: int,
    db: DB,
    current_company: CurrentCompany,
):
    _assert_company_owns_posting(db, posting_id, current_company.CompanyID)
    _get_package_or_404(db, pkg_id, posting_id)
    question = _get_question_or_404(db, question_id, pkg_id)
    db.delete(question)
    db.commit()


# ===========================================================================
# PRIVATE HELPERS
# ===========================================================================

def _get_department_or_404(db: Session, dept_id: int) -> Department:
    dept = db.query(Department).filter(Department.DepartmentID == dept_id).first()
    if dept is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with ID {dept_id} not found.",
        )
    return dept


def _get_posting_or_404(db: Session, posting_id: int) -> JobPosting:
    posting = db.query(JobPosting).filter(JobPosting.PostingID == posting_id).first()
    if posting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"JobPosting with ID {posting_id} not found.",
        )
    return posting


def _assert_company_owns_posting(db: Session, posting_id: int, company_id: int) -> JobPosting:
    """
    Fetches the posting and verifies ownership.
    Returns the posting so callers can reuse it without a second query.

    404 → posting does not exist at all.
    403 → posting exists but belongs to a different company.
    """
    posting = _get_posting_or_404(db, posting_id)
    if posting.CompanyID != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to manage this job posting.",
        )
    return posting


def _get_package_or_404(db: Session, pkg_id: int, posting_id: int) -> QuestionPackage:
    """
    Fetches a package and verifies it belongs to the given posting.
    This prevents path-traversal: POST /postings/1/packages/99/questions
    where package 99 actually belongs to posting 2.
    """
    package = db.query(QuestionPackage).filter(QuestionPackage.PackageID == pkg_id).first()
    if package is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"QuestionPackage with ID {pkg_id} not found.",
        )
    if package.PostingID != posting_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"QuestionPackage {pkg_id} does not belong to posting {posting_id}.",
        )
    return package


def _get_question_or_404(db: Session, question_id: int, pkg_id: int) -> Question:
    """Fetches a question and verifies it belongs to the given package."""
    question = db.query(Question).filter(Question.QuestionID == question_id).first()
    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question with ID {question_id} not found.",
        )
    if question.PackageID != pkg_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question {question_id} does not belong to package {pkg_id}.",
        )
    return question
