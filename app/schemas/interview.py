"""
schemas/interview.py
--------------------
Pydantic schemas for the Application and VideoInterview domain.
"""

from typing import Optional
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, HttpUrl, field_validator

from app.schemas.base import OrmBase


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
APPLICATION_STATUSES = {"Pending", "Reviewed", "Shortlisted", "Rejected", "Hired"}


class ApplicationCreate(BaseModel):
    PostingID: int = Field(..., gt=0)
    # SeekerID is taken from the authenticated JWT — never trusted from body


class ApplicationStatusUpdate(BaseModel):
    """Used by a Company reviewer to advance the application status."""
    Status: str = Field(..., max_length=50)

    @field_validator("Status")
    @classmethod
    def status_must_be_valid(cls, v: str) -> str:
        if v not in APPLICATION_STATUSES:
            raise ValueError(
                f"Status must be one of: {', '.join(sorted(APPLICATION_STATUSES))}"
            )
        return v


class ApplicationOut(OrmBase):
    ApplicationID:   int
    SeekerID:        int
    PostingID:       int
    ApplicationDate: Optional[datetime] = None
    Status:          str


# ---------------------------------------------------------------------------
# VideoInterview
# ---------------------------------------------------------------------------
class VideoInterviewCreate(BaseModel):
    ApplicationID: int    = Field(..., gt=0)
    PackageID:     int    = Field(..., gt=0)
    # Rule: video stored as URL string — no binary blobs
    VideoURL:      Optional[str] = Field(None, max_length=255,
                                         description="URL pointing to the hosted video resource")


class VideoInterviewReview(BaseModel):
    """Payload for a reviewer to add score and notes."""
    Score:         Optional[Decimal] = Field(None, ge=0, le=999.99)
    ReviewerNotes: Optional[str]     = None


class VideoInterviewOut(OrmBase):
    InterviewID:   int
    ApplicationID: int
    PackageID:     int
    VideoURL:      Optional[str]    = None
    Score:         Optional[Decimal] = None
    ReviewerNotes: Optional[str]    = None
