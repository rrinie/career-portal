"""
models/models.py
----------------
SQLAlchemy ORM models that mirror the PostgreSQL schema EXACTLY.

Rules enforced:
  - Table names match schema.sql (PascalCase, e.g. "Company", "JobSeeker")
  - Column names match schema.sql verbatim (PascalCase columns)
  - Primary keys use Integer + autoincrement (SERIAL in Postgres)
  - No UUIDs
  - VideoURL is a plain String — no binary blobs
  - All foreign keys and ON DELETE behaviours match schema.sql
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


# ---------------------------------------------------------------------------
# 1. Company
# ---------------------------------------------------------------------------
class Company(Base):
    __tablename__ = "company"

    CompanyID     = Column(Integer, primary_key=True, autoincrement=True)
    CompanyName   = Column(String(100), nullable=False)
    Industry      = Column(String(50))
    City          = Column(String(50))
    ContactEmail  = Column(String(100), unique=True, nullable=False)
    PasswordHash = Column(String(255), nullable=False)
    # Relationships
    job_postings  = relationship("JobPosting", back_populates="company",
                                 cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# 2. Department
# ---------------------------------------------------------------------------
class Department(Base):
    __tablename__ = "department"

    DepartmentID   = Column(Integer, primary_key=True, autoincrement=True)
    DepartmentName = Column(String(100), nullable=False)

    # Relationships
    positions = relationship("Position", back_populates="department")


# ---------------------------------------------------------------------------
# 3. Position
# ---------------------------------------------------------------------------
class Position(Base):
    __tablename__ = "position"

    PositionID   = Column(Integer, primary_key=True, autoincrement=True)
    DepartmentID = Column(Integer, ForeignKey("department.DepartmentID"), nullable=False)
    PositionName = Column(String(100), nullable=False)

    # Relationships
    department   = relationship("Department", back_populates="positions")
    job_postings = relationship("JobPosting", back_populates="position")


# ---------------------------------------------------------------------------
# 4. JobSeeker
# ---------------------------------------------------------------------------
class JobSeeker(Base):
    __tablename__ = "jobseeker"

    SeekerID     = Column(Integer, primary_key=True, autoincrement=True)
    FirstName    = Column(String(50), nullable=False)
    LastName     = Column(String(50), nullable=False)
    Email        = Column(String(100), unique=True, nullable=False)
    PasswordHash = Column(String(255), nullable=False)
    Phone        = Column(String(20))

    # Relationships
    cv_profile   = relationship("CV_Profile", back_populates="seeker",
                                uselist=False, cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="seeker",
                                cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# 5. CV_Profile
# ---------------------------------------------------------------------------
class CV_Profile(Base):
    __tablename__ = "cv_profile"

    ProfileID       = Column(Integer, primary_key=True, autoincrement=True)
    SeekerID        = Column(Integer, ForeignKey("jobseeker.SeekerID", ondelete="CASCADE"),
                             unique=True, nullable=False)
    EducationLevel  = Column(String(50))
    ExperienceYears = Column(Integer)
    LinkedInURL     = Column(String(255))
    Summary         = Column(Text)

    # Relationships
    seeker = relationship("JobSeeker", back_populates="cv_profile")


# ---------------------------------------------------------------------------
# 6. JobPosting
# ---------------------------------------------------------------------------
class JobPosting(Base):
    __tablename__ = "jobposting"

    PostingID  = Column(Integer, primary_key=True, autoincrement=True)
    CompanyID  = Column(Integer, ForeignKey("company.CompanyID", ondelete="CASCADE"),
                        nullable=False)
    PositionID = Column(Integer, ForeignKey("position.PositionID"), nullable=False)
    Title      = Column(String(100), nullable=False)
    WorkType   = Column(String(50))
    Deadline   = Column(Date)

    # Relationships
    company          = relationship("Company", back_populates="job_postings")
    position         = relationship("Position", back_populates="job_postings")
    question_packages = relationship("QuestionPackage", back_populates="job_posting",
                                     cascade="all, delete-orphan")
    applications     = relationship("Application", back_populates="job_posting",
                                    cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# 7. QuestionPackage
# ---------------------------------------------------------------------------
class QuestionPackage(Base):
    __tablename__ = "questionpackage"

    PackageID        = Column(Integer, primary_key=True, autoincrement=True)
    PostingID        = Column(Integer, ForeignKey("jobposting.PostingID", ondelete="CASCADE"),
                              nullable=False)
    PackageName      = Column(String(100))
    TimeLimitMinutes = Column(Integer)

    # Relationships
    job_posting      = relationship("JobPosting", back_populates="question_packages")
    questions        = relationship("Question", back_populates="package",
                                    cascade="all, delete-orphan")
    video_interviews = relationship("VideoInterview", back_populates="package")


# ---------------------------------------------------------------------------
# 8. Question
# ---------------------------------------------------------------------------
class Question(Base):
    __tablename__ = "question"

    QuestionID   = Column(Integer, primary_key=True, autoincrement=True)
    PackageID    = Column(Integer, ForeignKey("questionpackage.PackageID", ondelete="CASCADE"),
                          nullable=False)
    QuestionText = Column(Text, nullable=False)
    Points       = Column(Integer)

    # Relationships
    package = relationship("QuestionPackage", back_populates="questions")


# ---------------------------------------------------------------------------
# 9. Application
# ---------------------------------------------------------------------------
class Application(Base):
    __tablename__ = "application"

    ApplicationID   = Column(Integer, primary_key=True, autoincrement=True)
    SeekerID        = Column(Integer, ForeignKey("jobseeker.SeekerID", ondelete="CASCADE"),
                             nullable=False)
    PostingID       = Column(Integer, ForeignKey("jobposting.PostingID", ondelete="CASCADE"),
                             nullable=False)
    ApplicationDate = Column(DateTime, server_default=func.now())
    Status          = Column(String(50), default="Pending")

    # Relationships
    seeker           = relationship("JobSeeker", back_populates="applications")
    job_posting      = relationship("JobPosting", back_populates="applications")
    video_interviews = relationship("VideoInterview", back_populates="application",
                                    cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# 10. VideoInterview
# ---------------------------------------------------------------------------
class VideoInterview(Base):
    __tablename__ = "videointerview"

    InterviewID   = Column(Integer, primary_key=True, autoincrement=True)
    ApplicationID = Column(Integer, ForeignKey("application.ApplicationID", ondelete="CASCADE"),
                           nullable=False)
    PackageID     = Column(Integer, ForeignKey("questionpackage.PackageID"), nullable=False)
    # Rule: video stored as URL string — never a binary blob
    VideoURL      = Column(String(255))
    Score         = Column(Numeric(5, 2))
    ReviewerNotes = Column(Text)

    # Relationships
    application = relationship("Application", back_populates="video_interviews")
    package     = relationship("QuestionPackage", back_populates="video_interviews")
