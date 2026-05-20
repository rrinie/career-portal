"""
Pydantic v2 schemas for Application and VideoInterview.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.schemas.base import OrmBase


APPLICATION_STATUSES = {
    "Pending",
    "Reviewed",
    "Invited_To_Interview",
    "Accepted",
    "Rejected",
}


class ApplicationBase(BaseModel):
    SeekerID: int = Field(..., gt=0)
    PostingID: int = Field(..., gt=0)
    Status: str = Field("Pending", max_length=50)

    @field_validator("Status")
    @classmethod
    def status_must_be_valid(cls, value: str) -> str:
        if value not in APPLICATION_STATUSES:
            allowed = ", ".join(sorted(APPLICATION_STATUSES))
            raise ValueError(f"Status must be one of: {allowed}")
        return value


class ApplicationCreate(BaseModel):
    PostingID: int = Field(..., gt=0)


class ApplicationUpdate(BaseModel):
    Status: str | None = Field(None, max_length=50)

    @field_validator("Status")
    @classmethod
    def status_must_be_valid(cls, value: str | None) -> str | None:
        if value is not None and value not in APPLICATION_STATUSES:
            allowed = ", ".join(sorted(APPLICATION_STATUSES))
            raise ValueError(f"Status must be one of: {allowed}")
        return value


class ApplicationStatusUpdate(BaseModel):
    Status: str = Field(..., max_length=50)

    @field_validator("Status")
    @classmethod
    def status_must_be_valid(cls, value: str) -> str:
        if value not in APPLICATION_STATUSES:
            allowed = ", ".join(sorted(APPLICATION_STATUSES))
            raise ValueError(f"Status must be one of: {allowed}")
        return value


class ApplicationOut(OrmBase):
    ApplicationID: int
    SeekerID: int
    PostingID: int
    ApplicationDate: datetime
    Status: str


class VideoInterviewBase(BaseModel):
    ApplicationID: int = Field(..., gt=0)
    PackageID: int = Field(..., gt=0)
    VideoURL: str | None = Field(None, max_length=255)
    Score: Decimal | None = Field(
        None,
        ge=Decimal("0"),
        le=Decimal("999.99"),
        max_digits=5,
        decimal_places=2,
    )
    ReviewerNotes: str | None = None


class VideoInterviewCreate(BaseModel):
    ApplicationID: int = Field(..., gt=0)
    PackageID: int = Field(..., gt=0)
    VideoURL: str | None = Field(None, max_length=255)


class VideoInterviewUpdate(BaseModel):
    ApplicationID: int | None = Field(None, gt=0)
    PackageID: int | None = Field(None, gt=0)
    VideoURL: str | None = Field(None, max_length=255)
    Score: Decimal | None = Field(
        None,
        ge=Decimal("0"),
        le=Decimal("999.99"),
        max_digits=5,
        decimal_places=2,
    )
    ReviewerNotes: str | None = None


class VideoInterviewReview(BaseModel):
    Score: Decimal | None = Field(
        None,
        ge=Decimal("0"),
        le=Decimal("999.99"),
        max_digits=5,
        decimal_places=2,
    )
    ReviewerNotes: str | None = None


class VideoInterviewOut(OrmBase):
    InterviewID: int
    ApplicationID: int
    PackageID: int
    VideoURL: str | None = None
    Score: Decimal | None = None
    ReviewerNotes: str | None = None
