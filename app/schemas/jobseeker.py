"""
schemas/jobseeker.py
--------------------
Pydantic schemas for the JobSeeker and CV_Profile domain.

Naming convention:
  <Entity>Create  – payload accepted on POST (never exposes PasswordHash)
  <Entity>Update  – payload accepted on PATCH  (all fields Optional)
  <Entity>Out     – safe response shape (never exposes PasswordHash)
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.base import OrmBase


# ---------------------------------------------------------------------------
# CV_Profile  (nested inside JobSeekerOut)
# ---------------------------------------------------------------------------
class CV_ProfileCreate(BaseModel):
    EducationLevel:  Optional[str]  = None
    ExperienceYears: Optional[int]  = Field(None, ge=0)
    LinkedInURL:     Optional[str]  = None
    Summary:         Optional[str]  = None


class CV_ProfileUpdate(BaseModel):
    EducationLevel:  Optional[str]  = None
    ExperienceYears: Optional[int]  = Field(None, ge=0)
    LinkedInURL:     Optional[str]  = None
    Summary:         Optional[str]  = None


class CV_ProfileOut(OrmBase):
    ProfileID:       int
    SeekerID:        int
    EducationLevel:  Optional[str]  = None
    ExperienceYears: Optional[int]  = None
    LinkedInURL:     Optional[str]  = None
    Summary:         Optional[str]  = None


# ---------------------------------------------------------------------------
# JobSeeker — Register
# ---------------------------------------------------------------------------
class JobSeekerCreate(BaseModel):
    FirstName: str = Field(..., min_length=1, max_length=50)
    LastName:  str = Field(..., min_length=1, max_length=50)
    Email:     EmailStr
    Password:  str = Field(..., min_length=8, description="Plain-text password — hashed before storage")
    Phone:     Optional[str] = Field(None, max_length=20)

    @field_validator("Password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        return v


# ---------------------------------------------------------------------------
# JobSeeker — Update (PATCH)
# ---------------------------------------------------------------------------
class JobSeekerUpdate(BaseModel):
    FirstName: Optional[str] = Field(None, min_length=1, max_length=50)
    LastName:  Optional[str] = Field(None, min_length=1, max_length=50)
    Phone:     Optional[str] = Field(None, max_length=20)


# ---------------------------------------------------------------------------
# JobSeeker — Response (PasswordHash is NEVER included)
# ---------------------------------------------------------------------------
class JobSeekerOut(OrmBase):
    SeekerID:  int
    FirstName: str
    LastName:  str
    Email:     str
    Phone:     Optional[str] = None
    cv_profile: Optional[CV_ProfileOut] = None
