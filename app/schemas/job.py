"""
Pydantic v2 schemas for Department, Position, JobPosting,
QuestionPackage, and Question.
"""

from datetime import date

from pydantic import BaseModel, Field

from app.schemas.base import OrmBase


class DepartmentBase(BaseModel):
    DepartmentName: str = Field(..., min_length=1, max_length=100)


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    DepartmentName: str | None = Field(None, min_length=1, max_length=100)


class DepartmentOut(OrmBase):
    DepartmentID: int
    DepartmentName: str


class PositionBase(BaseModel):
    DepartmentID: int = Field(..., gt=0)
    PositionName: str = Field(..., min_length=1, max_length=100)


class PositionCreate(BaseModel):
    PositionName: str = Field(..., min_length=1, max_length=100)


class PositionUpdate(BaseModel):
    DepartmentID: int | None = Field(None, gt=0)
    PositionName: str | None = Field(None, min_length=1, max_length=100)


class PositionOut(OrmBase):
    PositionID: int
    DepartmentID: int
    PositionName: str


class QuestionBase(BaseModel):
    PackageID: int = Field(..., gt=0)
    QuestionText: str = Field(..., min_length=1)
    Points: int | None = Field(None, ge=0)


class QuestionCreate(BaseModel):
    QuestionText: str = Field(..., min_length=1)
    Points: int | None = Field(None, ge=0)


class QuestionUpdate(BaseModel):
    QuestionText: str | None = Field(None, min_length=1)
    Points: int | None = Field(None, ge=0)


class QuestionOut(OrmBase):
    QuestionID: int
    PackageID: int
    QuestionText: str
    Points: int | None = None


class QuestionPackageBase(BaseModel):
    PostingID: int = Field(..., gt=0)
    PackageName: str | None = Field(None, max_length=100)
    TimeLimitMinutes: int | None = Field(None, ge=1)


class QuestionPackageCreate(BaseModel):
    PackageName: str | None = Field(None, max_length=100)
    TimeLimitMinutes: int | None = Field(None, ge=1)


class QuestionPackageUpdate(BaseModel):
    PackageName: str | None = Field(None, max_length=100)
    TimeLimitMinutes: int | None = Field(None, ge=1)


class QuestionPackageOut(OrmBase):
    PackageID: int
    PostingID: int
    PackageName: str | None = None
    TimeLimitMinutes: int | None = None
    questions: list[QuestionOut] = Field(default_factory=list)


class JobPostingBase(BaseModel):
    CompanyID: int = Field(..., gt=0)
    PositionID: int = Field(..., gt=0)
    Title: str = Field(..., min_length=1, max_length=100)
    WorkType: str | None = Field(None, max_length=50)
    Deadline: date | None = None


class JobPostingCreate(BaseModel):
    PositionID: int = Field(..., gt=0)
    Title: str = Field(..., min_length=1, max_length=100)
    WorkType: str | None = Field(None, max_length=50)
    Deadline: date | None = None


class JobPostingUpdate(BaseModel):
    PositionID: int | None = Field(None, gt=0)
    Title: str | None = Field(None, min_length=1, max_length=100)
    WorkType: str | None = Field(None, max_length=50)
    Deadline: date | None = None


class JobPostingOut(OrmBase):
    PostingID: int
    CompanyID: int
    PositionID: int
    Title: str
    WorkType: str | None = None
    Deadline: date | None = None
    question_packages: list[QuestionPackageOut] = Field(default_factory=list)
