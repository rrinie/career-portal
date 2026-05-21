"""
seed.py
-------
Standalone database seeder for the normalized Career Portal schema.

Usage from the project root:
    python seed.py

The script is intentionally re-runnable: it wipes the 10 application tables in
reverse dependency order, then inserts fresh data while relying on database
assigned primary keys. Passwords are hashed before inserting JobSeeker and
Company rows.
"""

from __future__ import annotations

import os
import sys
from datetime import date, timedelta
from decimal import Decimal

from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Load .env before importing app config/database modules.
load_dotenv()

# Make sure the app package is importable when running `python seed.py`.
sys.path.insert(0, os.path.dirname(__file__))

from app.core.security import hash_password as get_password_hash
from app.database import Base, SessionLocal, engine
from app.models.models import (
    Application,
    CV_Profile,
    Company,
    Department,
    JobPosting,
    JobSeeker,
    Position,
    Question,
    QuestionPackage,
    VideoInterview,
)


TEST_CREDENTIALS = [
    ("JobSeeker", "alex.morgan@email.com", "Password1"),
    ("JobSeeker", "jordan.lee@email.com", "Password2"),
    ("Company", "hr@technova.io", "Company11"),
    ("Company", "careers@brightpath.co", "Company22"),
]


def wipe_existing(db: Session) -> None:
    """Delete rows in reverse foreign-key dependency order."""
    print("  Wiping existing data...")
    for model in (
        VideoInterview,
        Application,
        Question,
        QuestionPackage,
        JobPosting,
        CV_Profile,
        JobSeeker,
        Position,
        Department,
        Company,
    ):
        db.query(model).delete(synchronize_session=False)
    db.commit()


def seed(db: Session) -> None:
    today = date.today()

    print("  [1/10] Creating companies...")
    technova = Company(
        CompanyName="TechNova",
        Industry="Software",
        City="San Francisco",
        ContactEmail="hr@technova.io",
        PasswordHash=get_password_hash("Company11"),
    )
    brightpath = Company(
        CompanyName="BrightPath",
        Industry="EdTech",
        City="Austin",
        ContactEmail="careers@brightpath.co",
        PasswordHash=get_password_hash("Company22"),
    )
    db.add_all([technova, brightpath])

    print("  [2/10] Creating departments...")
    engineering = Department(DepartmentName="Engineering")
    product = Department(DepartmentName="Product")
    marketing = Department(DepartmentName="Marketing")
    db.add_all([engineering, product, marketing])
    db.flush()

    print("  [3/10] Creating positions...")
    backend = Position(department=engineering, PositionName="Backend Engineer")
    ml = Position(department=engineering, PositionName="Machine Learning Engineer")
    full_stack = Position(department=engineering, PositionName="Full Stack Developer")
    product_manager = Position(department=product, PositionName="Product Manager")
    ux_designer = Position(department=product, PositionName="UX Designer")
    growth = Position(department=marketing, PositionName="Growth Marketer")
    db.add_all([backend, ml, full_stack, product_manager, ux_designer, growth])
    db.flush()

    print("  [4/10] Creating job seekers...")
    alex = JobSeeker(
        FirstName="Alex",
        LastName="Morgan",
        Email="alex.morgan@email.com",
        PasswordHash=get_password_hash("Password1"),
        Phone="+1-415-555-0101",
    )
    jordan = JobSeeker(
        FirstName="Jordan",
        LastName="Lee",
        Email="jordan.lee@email.com",
        PasswordHash=get_password_hash("Password2"),
        Phone="+1-512-555-0188",
    )
    db.add_all([alex, jordan])
    db.flush()

    print("  [5/10] Creating CV profiles...")
    db.add_all([
        CV_Profile(
            seeker=alex,
            EducationLevel="Bachelor's",
            ExperienceYears=4,
            LinkedInURL="https://linkedin.com/in/alexmorgan-dev",
            Summary=(
                "Python backend engineer with experience building scalable APIs, "
                "data pipelines, and production services."
            ),
        ),
        CV_Profile(
            seeker=jordan,
            EducationLevel="Master's",
            ExperienceYears=2,
            LinkedInURL="https://linkedin.com/in/jordanlee-pm",
            Summary=(
                "Product-minded HCI graduate focused on discovery, UX research, "
                "and EdTech product delivery."
            ),
        ),
    ])

    print("  [6/10] Creating job postings...")
    backend_posting = JobPosting(
        company=technova,
        position=backend,
        Title="Senior Backend Engineer",
        WorkType="Hybrid",
        Deadline=today + timedelta(days=30),
    )
    ml_posting = JobPosting(
        company=technova,
        position=ml,
        Title="Machine Learning Engineer",
        WorkType="Remote",
        Deadline=today + timedelta(days=21),
    )
    full_stack_posting = JobPosting(
        company=technova,
        position=full_stack,
        Title="Full Stack Developer",
        WorkType="Remote",
        Deadline=today + timedelta(days=35),
    )
    pm_posting = JobPosting(
        company=brightpath,
        position=product_manager,
        Title="Associate Product Manager",
        WorkType="On-site",
        Deadline=today + timedelta(days=14),
    )
    growth_posting = JobPosting(
        company=brightpath,
        position=growth,
        Title="Growth Marketer - University Partnerships",
        WorkType="Hybrid",
        Deadline=today + timedelta(days=45),
    )
    db.add_all([
        backend_posting,
        ml_posting,
        full_stack_posting,
        pm_posting,
        growth_posting,
    ])
    db.flush()

    print("  [7/10] Creating question packages...")
    backend_package = QuestionPackage(
        job_posting=backend_posting,
        PackageName="Backend Technical Screen",
        TimeLimitMinutes=20,
    )
    ml_package = QuestionPackage(
        job_posting=ml_posting,
        PackageName="ML Fundamentals Screen",
        TimeLimitMinutes=25,
    )
    full_stack_package = QuestionPackage(
        job_posting=full_stack_posting,
        PackageName="Full Stack Practical Screen",
        TimeLimitMinutes=20,
    )
    pm_package = QuestionPackage(
        job_posting=pm_posting,
        PackageName="Product Thinking Screen",
        TimeLimitMinutes=15,
    )
    growth_package = QuestionPackage(
        job_posting=growth_posting,
        PackageName="Growth Strategy Screen",
        TimeLimitMinutes=15,
    )
    db.add_all([
        backend_package,
        ml_package,
        full_stack_package,
        pm_package,
        growth_package,
    ])
    db.flush()

    print("  [8/10] Creating questions...")
    questions_by_package = {
        backend_package: [
            ("Design a REST API for a high-traffic job board. What are your key tradeoffs?", 10),
            ("Explain concurrency vs. parallelism and how you have used async work in production.", 10),
            ("Describe a backend performance issue you diagnosed and fixed.", 5),
        ],
        ml_package: [
            ("Explain the bias-variance tradeoff with a practical example.", 10),
            ("How would you handle a heavily imbalanced classification dataset?", 10),
            ("How do you monitor a deployed model for drift?", 10),
        ],
        full_stack_package: [
            ("How would you structure a React and FastAPI feature from API contract to UI state?", 10),
            ("Describe how you handle authentication tokens safely in a browser app.", 10),
            ("What testing layers would you add for a job application workflow?", 5),
        ],
        pm_package: [
            ("How would you prioritize a backlog with competing stakeholder requests?", 10),
            ("Pick a product you admire and define three success metrics for it.", 10),
            ("Tell us about a feature that underperformed and what you learned.", 5),
        ],
        growth_package: [
            ("Describe a growth experiment you designed, including hypothesis and result.", 10),
            ("How would you build university partnerships from scratch with a small budget?", 10),
            ("What does sustainable growth mean beyond vanity metrics?", 5),
        ],
    }
    for package, package_questions in questions_by_package.items():
        db.add_all([
            Question(package=package, QuestionText=text, Points=points)
            for text, points in package_questions
        ])
    db.flush()

    print("  [9/10] Creating applications...")
    alex_backend_application = Application(
        seeker=alex,
        job_posting=backend_posting,
        Status="Invited_To_Interview",
    )
    alex_ml_application = Application(
        seeker=alex,
        job_posting=ml_posting,
        Status="Pending",
    )
    alex_full_stack_application = Application(
        seeker=alex,
        job_posting=full_stack_posting,
        Status="Reviewed",
    )
    jordan_pm_application = Application(
        seeker=jordan,
        job_posting=pm_posting,
        Status="Pending",
    )
    jordan_growth_application = Application(
        seeker=jordan,
        job_posting=growth_posting,
        Status="Rejected",
    )
    db.add_all([
        alex_backend_application,
        alex_ml_application,
        alex_full_stack_application,
        jordan_pm_application,
        jordan_growth_application,
    ])
    db.flush()

    print("  [10/10] Creating video interviews...")
    db.add_all([
        VideoInterview(
            application=alex_backend_application,
            package=backend_package,
            VideoURL="https://storage.example.com/interviews/alex-backend-screen.mp4",
            Score=Decimal("87.50"),
            ReviewerNotes=(
                "Strong system design instincts and clear communication. "
                "Recommend advancing to the technical interview."
            ),
        ),
        VideoInterview(
            application=alex_ml_application,
            package=ml_package,
            VideoURL="https://storage.example.com/interviews/alex-ml-screen.mp4",
            Score=None,
            ReviewerNotes=None,
        ),
        VideoInterview(
            application=jordan_pm_application,
            package=pm_package,
            VideoURL="https://storage.example.com/interviews/jordan-pm-screen.mp4",
            Score=Decimal("78.25"),
            ReviewerNotes="Good product intuition. Needs deeper metrics detail in the next round.",
        ),
    ])


def print_summary(db: Session) -> None:
    rows = {
        "Company": db.query(Company).count(),
        "Department": db.query(Department).count(),
        "Position": db.query(Position).count(),
        "JobSeeker": db.query(JobSeeker).count(),
        "CV_Profile": db.query(CV_Profile).count(),
        "JobPosting": db.query(JobPosting).count(),
        "QuestionPackage": db.query(QuestionPackage).count(),
        "Question": db.query(Question).count(),
        "Application": db.query(Application).count(),
        "VideoInterview": db.query(VideoInterview).count(),
    }

    print("\n  Seed complete. Row counts:")
    for table, count in rows.items():
        print(f"  {table:<18} {count:>3}")

    print("\n  Test credentials:")
    for actor, email, password in TEST_CREDENTIALS:
        print(f"  {actor:<10} {email:<32} {password}")


def main() -> None:
    print("\n" + "=" * 60)
    print("  University Career Portal - Database Seeder")
    print("=" * 60 + "\n")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        wipe_existing(db)
        seed(db)
        db.commit()
        print_summary(db)
        print("\n" + "=" * 60 + "\n")
    except Exception as exc:
        db.rollback()
        print(f"\n  ERROR: Seed failed and was rolled back.\n  Detail: {exc}\n")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
