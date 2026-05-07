"""
seed.py
-------
Standalone database seeder for the University Career Portal.

Populates the database with realistic mock data across all 10 tables,
with hashed passwords so every test account is immediately usable in
the Swagger UI.

Usage (from the project root — same directory as this file):
    python seed.py

Requirements:
  - Your .env file must be present and DATABASE_URL must point to a
    running PostgreSQL instance.
  - All pip dependencies must be installed:
      pip install -r requirements.txt

What gets created:
  Departments  : 3  (Engineering, Product, Marketing)
  Positions    : 6  (2 per department)
  Companies    : 2  (TechNova, BrightPath)
  JobPostings  : 4  (2 per company)
  JobSeekers   : 2  (with CV profiles)
  Packages     : 4  (1 per posting, each with 3 questions)
  Questions    : 12
  Applications : 3  (seeker_1 applied to 3 jobs; seeker_2 applied to 1)
  Interviews   : 2  (seeker_1 submitted videos for 2 of their applications)

Test credentials
────────────────────────────────────────────────────────────────────────
  JobSeeker 1 │ email: alex.morgan@email.com     │ password: Password1
  JobSeeker 2 │ email: jordan.lee@email.com      │ password: Password2
  Company 1   │ email: hr@technova.io            │ password: Company11
  Company 2   │ email: careers@brightpath.co     │ password: Company22
────────────────────────────────────────────────────────────────────────
"""

import sys
import os
from datetime import date, timedelta

# ---------------------------------------------------------------------------
# Make sure 'app' is importable when running from the project root
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.orm import Session

from app.database import SessionLocal, engine
from app.models.models import (
    Base,
    Company,
    Department,
    Position,
    JobSeeker,
    CV_Profile,
    JobPosting,
    QuestionPackage,
    Question,
    Application,
    VideoInterview,
)
from app.core.security import hash_password


# ===========================================================================
# IDEMPOTENCY HELPER
# ===========================================================================

def _wipe_existing(db: Session) -> None:
    """
    Delete all existing seed rows in reverse FK-dependency order so the
    script is safely re-runnable. Cascades in the schema handle children,
    but we delete parents explicitly for clarity.
    """
    print("  Wiping existing data...")
    db.query(VideoInterview).delete()
    db.query(Application).delete()
    db.query(Question).delete()
    db.query(QuestionPackage).delete()
    db.query(JobPosting).delete()
    db.query(CV_Profile).delete()
    db.query(JobSeeker).delete()
    db.query(Company).delete()
    db.query(Position).delete()
    db.query(Department).delete()
    db.commit()
    print("  Done.\n")


# ===========================================================================
# SEED FUNCTION
# ===========================================================================

def seed(db: Session) -> None:

    # -----------------------------------------------------------------------
    # STEP 1 — DEPARTMENTS
    # -----------------------------------------------------------------------
    print("  [1/9] Creating departments...")

    dept_engineering = Department(DepartmentName="Engineering")
    dept_product     = Department(DepartmentName="Product")
    dept_marketing   = Department(DepartmentName="Marketing")

    db.add_all([dept_engineering, dept_product, dept_marketing])
    db.flush()   # assigns DepartmentID without committing — lets us reference FKs below


    # -----------------------------------------------------------------------
    # STEP 2 — POSITIONS
    # -----------------------------------------------------------------------
    print("  [2/9] Creating positions...")

    pos_backend   = Position(DepartmentID=dept_engineering.DepartmentID, PositionName="Backend Engineer")
    pos_ml        = Position(DepartmentID=dept_engineering.DepartmentID, PositionName="ML Engineer")
    pos_pm        = Position(DepartmentID=dept_product.DepartmentID,     PositionName="Product Manager")
    pos_designer  = Position(DepartmentID=dept_product.DepartmentID,     PositionName="UX Designer")
    pos_growth    = Position(DepartmentID=dept_marketing.DepartmentID,   PositionName="Growth Marketer")
    pos_content   = Position(DepartmentID=dept_marketing.DepartmentID,   PositionName="Content Strategist")

    db.add_all([pos_backend, pos_ml, pos_pm, pos_designer, pos_growth, pos_content])
    db.flush()


    # -----------------------------------------------------------------------
    # STEP 3 — COMPANIES
    # -----------------------------------------------------------------------
    print("  [3/9] Creating companies...")

    company_technova = Company(
        CompanyName  = "TechNova",
        Industry     = "Software",
        City         = "San Francisco",
        ContactEmail = "hr@technova.io",
        PasswordHash = hash_password("Company11"),
    )
    company_bright = Company(
        CompanyName  = "BrightPath",
        Industry     = "EdTech",
        City         = "Austin",
        ContactEmail = "careers@brightpath.co",
        PasswordHash = hash_password("Company22"),
    )

    db.add_all([company_technova, company_bright])
    db.flush()


    # -----------------------------------------------------------------------
    # STEP 4 — JOB POSTINGS
    # -----------------------------------------------------------------------
    print("  [4/9] Creating job postings...")

    today = date.today()

    # TechNova postings
    posting_backend = JobPosting(
        CompanyID  = company_technova.CompanyID,
        PositionID = pos_backend.PositionID,
        Title      = "Senior Backend Engineer (Python)",
        WorkType   = "Hybrid",
        Deadline   = today + timedelta(days=30),
    )
    posting_ml = JobPosting(
        CompanyID  = company_technova.CompanyID,
        PositionID = pos_ml.PositionID,
        Title      = "Machine Learning Engineer",
        WorkType   = "Remote",
        Deadline   = today + timedelta(days=21),
    )
    # BrightPath postings
    posting_pm = JobPosting(
        CompanyID  = company_bright.CompanyID,
        PositionID = pos_pm.PositionID,
        Title      = "Associate Product Manager",
        WorkType   = "On-site",
        Deadline   = today + timedelta(days=14),
    )
    posting_growth = JobPosting(
        CompanyID  = company_bright.CompanyID,
        PositionID = pos_growth.PositionID,
        Title      = "Growth Marketer — University Partnerships",
        WorkType   = "Remote",
        Deadline   = today + timedelta(days=45),
    )

    db.add_all([posting_backend, posting_ml, posting_pm, posting_growth])
    db.flush()


    # -----------------------------------------------------------------------
    # STEP 5 — QUESTION PACKAGES + QUESTIONS
    # -----------------------------------------------------------------------
    print("  [5/9] Creating question packages and questions...")

    # — Package for Senior Backend Engineer —
    pkg_backend = QuestionPackage(
        PostingID        = posting_backend.PostingID,
        PackageName      = "Technical Screening",
        TimeLimitMinutes = 20,
    )
    db.add(pkg_backend)
    db.flush()

    db.add_all([
        Question(PackageID=pkg_backend.PackageID, Points=10,
                 QuestionText="Walk us through how you would design a RESTful API for a high-traffic e-commerce platform. What are your key considerations?"),
        Question(PackageID=pkg_backend.PackageID, Points=10,
                 QuestionText="Explain the difference between concurrency and parallelism. How does Python's asyncio relate to this?"),
        Question(PackageID=pkg_backend.PackageID, Points=5,
                 QuestionText="Describe a time you significantly improved the performance of a backend service. What did you measure and what was the outcome?"),
    ])

    # — Package for ML Engineer —
    pkg_ml = QuestionPackage(
        PostingID        = posting_ml.PostingID,
        PackageName      = "ML Fundamentals Round",
        TimeLimitMinutes = 25,
    )
    db.add(pkg_ml)
    db.flush()

    db.add_all([
        Question(PackageID=pkg_ml.PackageID, Points=10,
                 QuestionText="What is the bias-variance tradeoff? Give a concrete example of how you would detect and address each."),
        Question(PackageID=pkg_ml.PackageID, Points=10,
                 QuestionText="Explain how you would handle a heavily imbalanced dataset in a binary classification problem."),
        Question(PackageID=pkg_ml.PackageID, Points=10,
                 QuestionText="Describe your experience with model deployment. How do you monitor a model in production for drift?"),
    ])

    # — Package for Associate Product Manager —
    pkg_pm = QuestionPackage(
        PostingID        = posting_pm.PostingID,
        PackageName      = "Product Thinking Interview",
        TimeLimitMinutes = 15,
    )
    db.add(pkg_pm)
    db.flush()

    db.add_all([
        Question(PackageID=pkg_pm.PackageID, Points=10,
                 QuestionText="How would you prioritise a product backlog when engineering capacity is limited and stakeholder requests are competing?"),
        Question(PackageID=pkg_pm.PackageID, Points=10,
                 QuestionText="Walk us through a product you admire. What metrics would you use to measure its success?"),
        Question(PackageID=pkg_pm.PackageID, Points=5,
                 QuestionText="Tell us about a feature you shipped that didn't perform as expected. What did you learn?"),
    ])

    # — Package for Growth Marketer —
    pkg_growth = QuestionPackage(
        PostingID        = posting_growth.PostingID,
        PackageName      = "Growth & Strategy Screen",
        TimeLimitMinutes = 15,
    )
    db.add(pkg_growth)
    db.flush()

    db.add_all([
        Question(PackageID=pkg_growth.PackageID, Points=10,
                 QuestionText="Describe a growth experiment you designed and ran. What was your hypothesis, execution, and result?"),
        Question(PackageID=pkg_growth.PackageID, Points=10,
                 QuestionText="How would you build a university partnership programme from scratch with a $10K budget?"),
        Question(PackageID=pkg_growth.PackageID, Points=5,
                 QuestionText="What does 'sustainable growth' mean to you, and how does it differ from vanity metric growth?"),
    ])

    db.flush()


    # -----------------------------------------------------------------------
    # STEP 6 — JOB SEEKERS
    # -----------------------------------------------------------------------
    print("  [6/9] Creating job seekers...")

    seeker_alex = JobSeeker(
        FirstName    = "Alex",
        LastName     = "Morgan",
        Email        = "alex.morgan@email.com",
        PasswordHash = hash_password("Password1"),
        Phone        = "+1-415-555-0101",
    )
    seeker_jordan = JobSeeker(
        FirstName    = "Jordan",
        LastName     = "Lee",
        Email        = "jordan.lee@email.com",
        PasswordHash = hash_password("Password2"),
        Phone        = "+1-512-555-0188",
    )

    db.add_all([seeker_alex, seeker_jordan])
    db.flush()


    # -----------------------------------------------------------------------
    # STEP 7 — CV PROFILES
    # -----------------------------------------------------------------------
    print("  [7/9] Creating CV profiles...")

    db.add(CV_Profile(
        SeekerID        = seeker_alex.SeekerID,
        EducationLevel  = "Bachelor's",
        ExperienceYears = 4,
        LinkedInURL     = "https://linkedin.com/in/alexmorgan-dev",
        Summary         = (
            "Experienced Python backend engineer with 4 years building scalable "
            "REST APIs and data pipelines. Passionate about clean architecture and "
            "developer tooling. Seeking senior IC roles in fast-moving product teams."
        ),
    ))

    db.add(CV_Profile(
        SeekerID        = seeker_jordan.SeekerID,
        EducationLevel  = "Master's",
        ExperienceYears = 2,
        LinkedInURL     = "https://linkedin.com/in/jordanlee-pm",
        Summary         = (
            "Product-minded generalist with an MS in HCI and 2 years of APM experience. "
            "Comfortable taking products from 0-to-1 and running structured discovery. "
            "Looking for PM roles in EdTech or consumer software."
        ),
    ))

    db.flush()


    # -----------------------------------------------------------------------
    # STEP 8 — APPLICATIONS
    # -----------------------------------------------------------------------
    print("  [8/9] Creating applications...")

    # Alex applies to all three TechNova + BrightPath PM roles
    app_alex_backend = Application(
        SeekerID  = seeker_alex.SeekerID,
        PostingID = posting_backend.PostingID,
        Status    = "Shortlisted",
    )
    app_alex_ml = Application(
        SeekerID  = seeker_alex.SeekerID,
        PostingID = posting_ml.PostingID,
        Status    = "Pending",
    )
    app_alex_growth = Application(
        SeekerID  = seeker_alex.SeekerID,
        PostingID = posting_growth.PostingID,
        Status    = "Reviewed",
    )
    # Jordan applies to the PM role — their speciality
    app_jordan_pm = Application(
        SeekerID  = seeker_jordan.SeekerID,
        PostingID = posting_pm.PostingID,
        Status    = "Pending",
    )

    db.add_all([app_alex_backend, app_alex_ml, app_alex_growth, app_jordan_pm])
    db.flush()


    # -----------------------------------------------------------------------
    # STEP 9 — VIDEO INTERVIEWS
    # -----------------------------------------------------------------------
    print("  [9/9] Creating video interview submissions...")

    # Alex has submitted a video for the Backend role (already scored by reviewer)
    db.add(VideoInterview(
        ApplicationID = app_alex_backend.ApplicationID,
        PackageID     = pkg_backend.PackageID,
        VideoURL      = "https://storage.example.com/interviews/alex-morgan-backend-screen.mp4",
        Score         = 87.50,
        ReviewerNotes = (
            "Strong system design instincts and clear communication. "
            "Async/concurrency answer was particularly sharp. "
            "Recommend advancing to technical interview."
        ),
    ))

    # Alex also submitted a video for the ML role (not yet reviewed)
    db.add(VideoInterview(
        ApplicationID = app_alex_ml.ApplicationID,
        PackageID     = pkg_ml.PackageID,
        VideoURL      = "https://storage.example.com/interviews/alex-morgan-ml-screen.mp4",
        Score         = None,
        ReviewerNotes = None,
    ))

    db.flush()


# ===========================================================================
# ENTRY POINT
# ===========================================================================

def main() -> None:
    print("\n" + "=" * 60)
    print("  University Career Portal — Database Seeder")
    print("=" * 60 + "\n")

    db: Session = SessionLocal()

    try:
        _wipe_existing(db)
        seed(db)
        db.commit()

        print("\n" + "=" * 60)
        print("  Seed complete. Summary:")
        print("=" * 60)

        rows = {
            "Departments":      db.query(Department).count(),
            "Positions":        db.query(Position).count(),
            "Companies":        db.query(Company).count(),
            "JobPostings":      db.query(JobPosting).count(),
            "QuestionPackages": db.query(QuestionPackage).count(),
            "Questions":        db.query(Question).count(),
            "JobSeekers":       db.query(JobSeeker).count(),
            "CV_Profiles":      db.query(CV_Profile).count(),
            "Applications":     db.query(Application).count(),
            "VideoInterviews":  db.query(VideoInterview).count(),
        }
        for table, count in rows.items():
            print(f"  {table:<22} {count:>3} row(s)")

        print("\n" + "-" * 60)
        print("  Test credentials (use in Swagger UI /docs)")
        print("-" * 60)
        credentials = [
            ("JobSeeker 1", "alex.morgan@email.com",    "Password1"),
            ("JobSeeker 2", "jordan.lee@email.com",     "Password2"),
            ("Company 1",   "hr@technova.io",           "Company11"),
            ("Company 2",   "careers@brightpath.co",    "Company22"),
        ]
        for actor, email, password in credentials:
            print(f"  {actor:<14}  {email:<32}  {password}")

        print("=" * 60 + "\n")

    except Exception as exc:
        db.rollback()
        print(f"\n  ERROR: Seed failed and was rolled back.\n  Detail: {exc}\n")
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
