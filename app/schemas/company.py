"""
schemas/company.py
------------------
Pydantic schemas for the Company domain.

Note: Company has no PasswordHash column in the schema — authentication
uses ContactEmail + a plain password that IS stored hashed in a separate
column we'll add via migration.  For now, the auth router uses a
'Password' field on CompanyCreate and the router hashes it before
persisting.  The out-schema never exposes it.

If you have already added a PasswordHash column to Company, this schema
matches that design.  If not, see the auth router comments.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field

from app.schemas.base import OrmBase


# ---------------------------------------------------------------------------
# Company — Register
# ---------------------------------------------------------------------------
class CompanyCreate(BaseModel):
    CompanyName:  str      = Field(..., min_length=1, max_length=100)
    Industry:     Optional[str] = Field(None, max_length=50)
    City:         Optional[str] = Field(None, max_length=50)
    ContactEmail: EmailStr
    Password:     str      = Field(..., min_length=8,
                                   description="Plain-text password — hashed before storage")


# ---------------------------------------------------------------------------
# Company — Update (PATCH)
# ---------------------------------------------------------------------------
class CompanyUpdate(BaseModel):
    CompanyName: Optional[str] = Field(None, min_length=1, max_length=100)
    Industry:    Optional[str] = Field(None, max_length=50)
    City:        Optional[str] = Field(None, max_length=50)


# ---------------------------------------------------------------------------
# Company — Response (PasswordHash never included)
# ---------------------------------------------------------------------------
class CompanyOut(OrmBase):
    CompanyID:    int
    CompanyName:  str
    Industry:     Optional[str] = None
    City:         Optional[str] = None
    ContactEmail: str
