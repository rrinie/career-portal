"""
schemas/base.py
---------------
Shared Pydantic config used by all response schemas.
from_attributes=True  →  allows Pydantic v2 to read from SQLAlchemy ORM objects.
"""

from pydantic import BaseModel, ConfigDict


class OrmBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
