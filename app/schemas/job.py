"""
schemas/job.py
--------------
Pydantic schemas for the job-posting domain:
  Department → Position → JobPosting → QuestionPackage → Question
"""

from typing import Optional
from datetime import date

from pydantic import BaseModel, Field

from app.schemas.base import OrmBase


# ---------------------------------------------------------------------------
# Department
# ---------------------------------------------------------------------------
class DepartmentCreate(BaseModel):
    DepartmentName: str = Field(..., min_length=1, max_length=100)


class DepartmentOut(OrmBase):
    DepartmentID:   int
    DepartmentName: str


# ---------------------------------------------------------------------------
# Position
# ---------------------------------------------------------------------------
class PositionCreate(BaseModel):
    DepartmentID: int = Field(..., gt=0)
    PositionName: str = Field(..., min_length=1, max_length=100)


class PositionOut(OrmBase):
    PositionID:   int
    DepartmentID: int
    PositionName: str


# ---------------------------------------------------------------------------
# Question  (defined before QuestionPackage so it can be nested)
# ---------------------------------------------------------------------------
class QuestionCreate(BaseModel):
    QuestionText: str = Field(..., min_length=1)
    Points:       Optional[int] = Field(None, ge=0)


class QuestionUpdate(BaseModel):
    QuestionText: Optional[str] = Field(None, min_length=1)
    Points:       Optional[int] = Field(None, ge=0)


class QuestionOut(OrmBase):
    QuestionID:   int
    PackageID:    int
    QuestionText: str
    Points:       Optional[int] = None


# ---------------------------------------------------------------------------
# QuestionPackage
# ---------------------------------------------------------------------------
class QuestionPackageCreate(BaseModel):
    PostingID:        int = Field(..., gt=0)
    PackageName:      Optional[str] = Field(None, max_length=100)
    TimeLimitMinutes: Optional[int] = Field(None, ge=1)


class QuestionPackageUpdate(BaseModel):
    PackageName:      Optional[str] = Field(None, max_length=100)
    TimeLimitMinutes: Optional[int] = Field(None, ge=1)


class QuestionPackageOut(OrmBase):
    PackageID:        int
    PostingID:        int
    PackageName:      Optional[str] = None
    TimeLimitMinutes: Optional[int] = None
    questions:        list[QuestionOut] = []


# ---------------------------------------------------------------------------
# JobPosting
# ---------------------------------------------------------------------------
WORK_TYPES = {"Remote", "Hybrid", "On-site"}


class JobPostingCreate(BaseModel):
    CompanyID:  int    = Field(..., gt=0)
    PositionID: int    = Field(..., gt=0)
    Title:      str    = Field(..., min_length=1, max_length=100)
    WorkType:   Optional[str] = Field(None, max_length=50)
    Deadline:   Optional[date] = None


class JobPostingUpdate(BaseModel):
    Title:    Optional[str]  = Field(None, min_length=1, max_length=100)
    WorkType: Optional[str]  = Field(None, max_length=50)
    Deadline: Optional[date] = None


class JobPostingOut(OrmBase):
    PostingID:  int
    CompanyID:  int
    PositionID: int
    Title:      str
    WorkType:   Optional[str]  = None
    Deadline:   Optional[date] = None
    question_packages: list[QuestionPackageOut] = []
