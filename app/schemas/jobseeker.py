"""
Pydantic v2 schemas for JobSeeker and CV_Profile.
"""

from pydantic import BaseModel, EmailStr, Field

from app.schemas.base import OrmBase


class CV_ProfileBase(BaseModel):
    EducationLevel: str | None = Field(None, max_length=50)
    ExperienceYears: int | None = Field(None, ge=0)
    LinkedInURL: str | None = Field(None, max_length=255)
    Summary: str | None = None


class CV_ProfileCreate(CV_ProfileBase):
    pass


class CV_ProfileUpdate(BaseModel):
    EducationLevel: str | None = Field(None, max_length=50)
    ExperienceYears: int | None = Field(None, ge=0)
    LinkedInURL: str | None = Field(None, max_length=255)
    Summary: str | None = None


class CV_ProfileOut(OrmBase):
    ProfileID: int
    SeekerID: int
    EducationLevel: str | None = None
    ExperienceYears: int | None = None
    LinkedInURL: str | None = Field(None, max_length=255)
    Summary: str | None = None


class JobSeekerBase(BaseModel):
    FirstName: str = Field(..., min_length=1, max_length=50)
    LastName: str = Field(..., min_length=1, max_length=50)
    Email: EmailStr
    Phone: str | None = Field(None, max_length=20)


class JobSeekerCreate(JobSeekerBase):
    Password: str = Field(..., min_length=8, max_length=255)


class JobSeekerUpdate(BaseModel):
    FirstName: str | None = Field(None, min_length=1, max_length=50)
    LastName: str | None = Field(None, min_length=1, max_length=50)
    Email: EmailStr | None = None
    Password: str | None = Field(None, min_length=8, max_length=255)
    Phone: str | None = Field(None, max_length=20)


class JobSeekerOut(OrmBase):
    SeekerID: int
    FirstName: str
    LastName: str
    Email: EmailStr
    Phone: str | None = None
    cv_profile: CV_ProfileOut | None = None


CVProfileBase = CV_ProfileBase
CVProfileCreate = CV_ProfileCreate
CVProfileUpdate = CV_ProfileUpdate
CVProfileOut = CV_ProfileOut
