"""
Public job board plus company-managed departments, positions, packages, and questions.
"""

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies import CurrentCompany, DB
from app.models.models import Department, JobPosting, Position, Question, QuestionPackage
from app.schemas.job import (
    DepartmentCreate,
    DepartmentOut,
    DepartmentUpdate,
    JobPostingOut,
    PositionCreate,
    PositionOut,
    PositionUpdate,
    QuestionCreate,
    QuestionOut,
    QuestionPackageCreate,
    QuestionPackageOut,
    QuestionPackageUpdate,
    QuestionUpdate,
)

router = APIRouter(prefix="/jobs", tags=["Job Board"])


@router.get("/departments", response_model=list[DepartmentOut], summary="List departments")
def list_departments(db: DB):
    return db.query(Department).order_by(Department.DepartmentName).all()


@router.post("/departments", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED, summary="Create a department")
def create_department(payload: DepartmentCreate, db: DB, _: CurrentCompany):
    department = Department(DepartmentName=payload.DepartmentName)
    db.add(department)
    db.commit()
    db.refresh(department)
    return department


@router.patch("/departments/{department_id}", response_model=DepartmentOut, summary="Update a department")
def update_department(department_id: int, payload: DepartmentUpdate, db: DB, _: CurrentCompany):
    department = _get_department_or_404(db, department_id)
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No updatable fields were provided.")
    for field, value in update_data.items():
        setattr(department, field, value)
    db.commit()
    db.refresh(department)
    return department


@router.get("/departments/{department_id}/positions", response_model=list[PositionOut], summary="List positions in a department")
def list_positions(department_id: int, db: DB):
    _get_department_or_404(db, department_id)
    return (
        db.query(Position)
        .filter(Position.DepartmentID == department_id)
        .order_by(Position.PositionName)
        .all()
    )


@router.post(
    "/departments/{department_id}/positions",
    response_model=PositionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a position",
)
def create_position(department_id: int, payload: PositionCreate, db: DB, _: CurrentCompany):
    _get_department_or_404(db, department_id)
    position = Position(DepartmentID=department_id, PositionName=payload.PositionName)
    db.add(position)
    db.commit()
    db.refresh(position)
    return position


@router.patch("/positions/{position_id}", response_model=PositionOut, summary="Update a position")
def update_position(position_id: int, payload: PositionUpdate, db: DB, _: CurrentCompany):
    position = _get_position_or_404(db, position_id)
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No updatable fields were provided.")
    if "DepartmentID" in update_data:
        _get_department_or_404(db, update_data["DepartmentID"])
    for field, value in update_data.items():
        setattr(position, field, value)
    db.commit()
    db.refresh(position)
    return position


@router.get("/postings", response_model=list[JobPostingOut], summary="Browse job postings")
def list_postings(
    db: DB,
    work_type: str | None = Query(None, description="Filter by WorkType"),
    position_id: int | None = Query(None, description="Filter by PositionID"),
    company_id: int | None = Query(None, description="Filter by CompanyID"),
):
    query = db.query(JobPosting)
    if work_type:
        query = query.filter(JobPosting.WorkType == work_type)
    if position_id:
        query = query.filter(JobPosting.PositionID == position_id)
    if company_id:
        query = query.filter(JobPosting.CompanyID == company_id)
    return query.order_by(JobPosting.PostingID.desc()).all()


@router.get("/postings/{posting_id}", response_model=JobPostingOut, summary="Get a job posting")
def get_posting(posting_id: int, db: DB):
    return _get_posting_or_404(db, posting_id)


@router.post(
    "/postings/{posting_id}/packages",
    response_model=QuestionPackageOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a question package",
)
def create_package(posting_id: int, payload: QuestionPackageCreate, db: DB, current_company: CurrentCompany):
    _assert_company_owns_posting(db, posting_id, current_company.CompanyID)
    package = QuestionPackage(
        PostingID=posting_id,
        PackageName=payload.PackageName,
        TimeLimitMinutes=payload.TimeLimitMinutes,
    )
    db.add(package)
    db.commit()
    db.refresh(package)
    return package


@router.get("/postings/{posting_id}/packages/{package_id}", response_model=QuestionPackageOut, summary="Get a question package")
def get_package(posting_id: int, package_id: int, db: DB, current_company: CurrentCompany):
    _assert_company_owns_posting(db, posting_id, current_company.CompanyID)
    return _get_package_or_404(db, package_id, posting_id)


@router.patch("/postings/{posting_id}/packages/{package_id}", response_model=QuestionPackageOut, summary="Update a question package")
def update_package(
    posting_id: int,
    package_id: int,
    payload: QuestionPackageUpdate,
    db: DB,
    current_company: CurrentCompany,
):
    _assert_company_owns_posting(db, posting_id, current_company.CompanyID)
    package = _get_package_or_404(db, package_id, posting_id)
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No updatable fields were provided.")
    for field, value in update_data.items():
        setattr(package, field, value)
    db.commit()
    db.refresh(package)
    return package


@router.delete("/postings/{posting_id}/packages/{package_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a question package")
def delete_package(posting_id: int, package_id: int, db: DB, current_company: CurrentCompany):
    _assert_company_owns_posting(db, posting_id, current_company.CompanyID)
    package = _get_package_or_404(db, package_id, posting_id)
    db.delete(package)
    db.commit()


@router.post(
    "/postings/{posting_id}/packages/{package_id}/questions",
    response_model=QuestionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a question",
)
def create_question(
    posting_id: int,
    package_id: int,
    payload: QuestionCreate,
    db: DB,
    current_company: CurrentCompany,
):
    _assert_company_owns_posting(db, posting_id, current_company.CompanyID)
    _get_package_or_404(db, package_id, posting_id)
    question = Question(
        PackageID=package_id,
        QuestionText=payload.QuestionText,
        Points=payload.Points,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


@router.patch(
    "/postings/{posting_id}/packages/{package_id}/questions/{question_id}",
    response_model=QuestionOut,
    summary="Update a question",
)
def update_question(
    posting_id: int,
    package_id: int,
    question_id: int,
    payload: QuestionUpdate,
    db: DB,
    current_company: CurrentCompany,
):
    _assert_company_owns_posting(db, posting_id, current_company.CompanyID)
    _get_package_or_404(db, package_id, posting_id)
    question = _get_question_or_404(db, question_id, package_id)
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No updatable fields were provided.")
    for field, value in update_data.items():
        setattr(question, field, value)
    db.commit()
    db.refresh(question)
    return question


@router.delete(
    "/postings/{posting_id}/packages/{package_id}/questions/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a question",
)
def delete_question(posting_id: int, package_id: int, question_id: int, db: DB, current_company: CurrentCompany):
    _assert_company_owns_posting(db, posting_id, current_company.CompanyID)
    _get_package_or_404(db, package_id, posting_id)
    question = _get_question_or_404(db, question_id, package_id)
    db.delete(question)
    db.commit()


def _get_department_or_404(db: Session, department_id: int) -> Department:
    department = db.query(Department).filter(Department.DepartmentID == department_id).first()
    if department is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Department with ID {department_id} not found.")
    return department


def _get_position_or_404(db: Session, position_id: int) -> Position:
    position = db.query(Position).filter(Position.PositionID == position_id).first()
    if position is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Position with ID {position_id} not found.")
    return position


def _get_posting_or_404(db: Session, posting_id: int) -> JobPosting:
    posting = db.query(JobPosting).filter(JobPosting.PostingID == posting_id).first()
    if posting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"JobPosting with ID {posting_id} not found.")
    return posting


def _assert_company_owns_posting(db: Session, posting_id: int, company_id: int) -> JobPosting:
    posting = _get_posting_or_404(db, posting_id)
    if posting.CompanyID != company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to manage this job posting.")
    return posting


def _get_package_or_404(db: Session, package_id: int, posting_id: int) -> QuestionPackage:
    package = db.query(QuestionPackage).filter(QuestionPackage.PackageID == package_id).first()
    if package is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"QuestionPackage with ID {package_id} not found.")
    if package.PostingID != posting_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"QuestionPackage {package_id} does not belong to posting {posting_id}.")
    return package


def _get_question_or_404(db: Session, question_id: int, package_id: int) -> Question:
    question = db.query(Question).filter(Question.QuestionID == question_id).first()
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Question with ID {question_id} not found.")
    if question.PackageID != package_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Question {question_id} does not belong to package {package_id}.")
    return question
