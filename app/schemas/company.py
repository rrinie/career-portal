"""
Pydantic v2 schemas for Company.
"""

from pydantic import BaseModel, EmailStr, Field

from app.schemas.base import OrmBase


class CompanyBase(BaseModel):
    CompanyName: str = Field(..., min_length=1, max_length=100)
    Industry: str | None = Field(None, max_length=50)
    City: str | None = Field(None, max_length=50)
    ContactEmail: EmailStr


class CompanyCreate(CompanyBase):
    Password: str = Field(..., min_length=8, max_length=255)


class CompanyUpdate(BaseModel):
    CompanyName: str | None = Field(None, min_length=1, max_length=100)
    Industry: str | None = Field(None, max_length=50)
    City: str | None = Field(None, max_length=50)
    ContactEmail: EmailStr | None = None
    Password: str | None = Field(None, min_length=8, max_length=255)


class CompanyOut(OrmBase):
    CompanyID: int
    CompanyName: str
    Industry: str | None = None
    City: str | None = None
    ContactEmail: EmailStr
