"""
SQLAlchemy ORM models for the normalized Career Portal schema.

The database engineer's MySQL AUTO_INCREMENT columns are represented with
PostgreSQL-compatible integer primary keys. SQLAlchemy will emit the correct
autoincrement/serial identity behavior for PostgreSQL dialects.
"""

from datetime import date as date_type, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Company(Base):
    __tablename__ = "Company"

    CompanyID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    CompanyName: Mapped[str] = mapped_column(String(100), nullable=False)
    Industry: Mapped[str | None] = mapped_column(String(50))
    City: Mapped[str | None] = mapped_column(String(50))
    ContactEmail: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    PasswordHash: Mapped[str] = mapped_column(String(255), nullable=False)

    job_postings: Mapped[list["JobPosting"]] = relationship(
        "JobPosting",
        back_populates="company",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Department(Base):
    __tablename__ = "Department"

    DepartmentID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    DepartmentName: Mapped[str] = mapped_column(String(100), nullable=False)

    positions: Mapped[list["Position"]] = relationship(
        "Position",
        back_populates="department",
    )


class Position(Base):
    __tablename__ = "Position"

    PositionID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    DepartmentID: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Department.DepartmentID"),
        nullable=False,
    )
    PositionName: Mapped[str] = mapped_column(String(100), nullable=False)

    department: Mapped["Department"] = relationship(
        "Department",
        back_populates="positions",
    )
    job_postings: Mapped[list["JobPosting"]] = relationship(
        "JobPosting",
        back_populates="position",
    )


class JobSeeker(Base):
    __tablename__ = "JobSeeker"

    SeekerID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    FirstName: Mapped[str] = mapped_column(String(50), nullable=False)
    LastName: Mapped[str] = mapped_column(String(50), nullable=False)
    Email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    PasswordHash: Mapped[str] = mapped_column(String(255), nullable=False)
    Phone: Mapped[str | None] = mapped_column(String(20))

    cv_profile: Mapped["CV_Profile | None"] = relationship(
        "CV_Profile",
        back_populates="seeker",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )
    applications: Mapped[list["Application"]] = relationship(
        "Application",
        back_populates="seeker",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    job_postings: Mapped[list["JobPosting"]] = relationship(
        "JobPosting",
        secondary="Application",
        back_populates="seekers",
        viewonly=True,
    )


class CV_Profile(Base):
    __tablename__ = "CV_Profile"

    ProfileID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    SeekerID: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("JobSeeker.SeekerID", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    EducationLevel: Mapped[str | None] = mapped_column(String(50))
    ExperienceYears: Mapped[int | None] = mapped_column(Integer)
    LinkedInURL: Mapped[str | None] = mapped_column(String(255))
    Summary: Mapped[str | None] = mapped_column(Text)

    seeker: Mapped["JobSeeker"] = relationship(
        "JobSeeker",
        back_populates="cv_profile",
    )


class JobPosting(Base):
    __tablename__ = "JobPosting"

    PostingID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    CompanyID: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Company.CompanyID", ondelete="CASCADE"),
        nullable=False,
    )
    PositionID: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Position.PositionID"),
        nullable=False,
    )
    Title: Mapped[str] = mapped_column(String(100), nullable=False)
    WorkType: Mapped[str | None] = mapped_column(String(50))
    Deadline: Mapped[date_type | None] = mapped_column(Date)

    company: Mapped["Company"] = relationship(
        "Company",
        back_populates="job_postings",
    )
    position: Mapped["Position"] = relationship(
        "Position",
        back_populates="job_postings",
    )
    question_packages: Mapped[list["QuestionPackage"]] = relationship(
        "QuestionPackage",
        back_populates="job_posting",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    applications: Mapped[list["Application"]] = relationship(
        "Application",
        back_populates="job_posting",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    seekers: Mapped[list["JobSeeker"]] = relationship(
        "JobSeeker",
        secondary="Application",
        back_populates="job_postings",
        viewonly=True,
    )


class QuestionPackage(Base):
    __tablename__ = "QuestionPackage"

    PackageID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    PostingID: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("JobPosting.PostingID", ondelete="CASCADE"),
        nullable=False,
    )
    PackageName: Mapped[str | None] = mapped_column(String(100))
    TimeLimitMinutes: Mapped[int | None] = mapped_column(Integer)

    job_posting: Mapped["JobPosting"] = relationship(
        "JobPosting",
        back_populates="question_packages",
    )
    questions: Mapped[list["Question"]] = relationship(
        "Question",
        back_populates="package",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    video_interviews: Mapped[list["VideoInterview"]] = relationship(
        "VideoInterview",
        back_populates="package",
    )


class Question(Base):
    __tablename__ = "Question"

    QuestionID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    PackageID: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("QuestionPackage.PackageID", ondelete="CASCADE"),
        nullable=False,
    )
    QuestionText: Mapped[str] = mapped_column(Text, nullable=False)
    Points: Mapped[int | None] = mapped_column(Integer)

    package: Mapped["QuestionPackage"] = relationship(
        "QuestionPackage",
        back_populates="questions",
    )


class Application(Base):
    __tablename__ = "Application"

    ApplicationID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    SeekerID: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("JobSeeker.SeekerID", ondelete="CASCADE"),
        nullable=False,
    )
    PostingID: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("JobPosting.PostingID", ondelete="CASCADE"),
        nullable=False,
    )
    ApplicationDate: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    Status: Mapped[str] = mapped_column(
        String(50),
        default="Pending",
        server_default="Pending",
        nullable=False,
    )

    seeker: Mapped["JobSeeker"] = relationship(
        "JobSeeker",
        back_populates="applications",
    )
    job_posting: Mapped["JobPosting"] = relationship(
        "JobPosting",
        back_populates="applications",
    )
    video_interviews: Mapped[list["VideoInterview"]] = relationship(
        "VideoInterview",
        back_populates="application",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class VideoInterview(Base):
    __tablename__ = "VideoInterview"

    InterviewID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ApplicationID: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Application.ApplicationID", ondelete="CASCADE"),
        nullable=False,
    )
    PackageID: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("QuestionPackage.PackageID"),
        nullable=False,
    )
    VideoURL: Mapped[str | None] = mapped_column(String(255))
    Score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    ReviewerNotes: Mapped[str | None] = mapped_column(Text)

    application: Mapped["Application"] = relationship(
        "Application",
        back_populates="video_interviews",
    )
    package: Mapped["QuestionPackage"] = relationship(
        "QuestionPackage",
        back_populates="video_interviews",
    )


CVProfile = CV_Profile
