import contextlib
import json
from datetime import datetime
from typing import Generator, List, Optional
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from app.config import logger, settings
from app.models import (
    AccountVerificationDB,
    ApplicationRunDB,
    Base,
    GenerationAttemptDB,
    LocalTestRunDB,
    ProblemDB,
    ProblemStatus,
    SubmissionDB,
    Verdict,
    VerificationStatus,
)

# SQLite foreign keys enforcement
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if "sqlite" in settings.DATABASE_URL:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Create Engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

if "sqlite" in settings.DATABASE_URL:
    event.listen(engine, "connect", _set_sqlite_pragma)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

def init_db() -> None:
    """Creates all database tables."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully.")

@contextlib.contextmanager
def get_db() -> Generator[Session, None, None]:
    """Context manager for acquiring and closing database sessions."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

class DatabaseManager:
    """High-level persistence helper for leetcode-automator."""

    @staticmethod
    def upsert_problem(
        slug: str,
        title: str,
        url: str,
        category: str,
        difficulty: str,
        order_index: int = 0,
        class_name: str = "Solution",
        method_name: Optional[str] = None,
        statement: Optional[str] = None,
        starter_code: Optional[str] = None,
        sample_test_case: Optional[str] = None,
        example_testcases: Optional[List[str]] = None,
    ) -> ProblemDB:
        with get_db() as db:
            problem = db.query(ProblemDB).filter_by(slug=slug).first()
            if not problem:
                problem = ProblemDB(
                    slug=slug,
                    title=title,
                    url=url,
                    category=category,
                    difficulty=difficulty,
                    order_index=order_index,
                    class_name=class_name,
                    method_name=method_name,
                    statement=statement,
                    starter_code=starter_code,
                    sample_test_case=sample_test_case,
                    example_testcases=json.dumps(example_testcases) if example_testcases else None,
                    status=ProblemStatus.PENDING.value,
                )
                db.add(problem)
            else:
                problem.title = title
                problem.url = url
                problem.category = category
                problem.difficulty = difficulty
                problem.order_index = order_index
                problem.class_name = class_name
                if method_name:
                    problem.method_name = method_name
                if statement:
                    problem.statement = statement
                if starter_code:
                    problem.starter_code = starter_code
                if sample_test_case:
                    problem.sample_test_case = sample_test_case
                if example_testcases:
                    problem.example_testcases = json.dumps(example_testcases)
            db.commit()
            db.refresh(problem)
            return problem

    @staticmethod
    def get_problem(slug: str) -> Optional[ProblemDB]:
        with get_db() as db:
            return db.query(ProblemDB).filter_by(slug=slug).first()

    @staticmethod
    def list_problems(status: Optional[str] = None) -> List[ProblemDB]:
        with get_db() as db:
            query = db.query(ProblemDB).order_index if hasattr(ProblemDB, "order_index") else db.query(ProblemDB)
            query = db.query(ProblemDB).order_by(ProblemDB.order_index.asc())
            if status:
                query = query.filter_by(status=status)
            return query.all()

    @staticmethod
    def update_problem_status(slug: str, status: ProblemStatus, solution_path: Optional[str] = None) -> None:
        with get_db() as db:
            problem = db.query(ProblemDB).filter_by(slug=slug).first()
            if problem:
                problem.status = status.value
                if solution_path:
                    problem.solution_code_path = solution_path
                problem.updated_at = datetime.utcnow()
                db.commit()

    @staticmethod
    def increment_retry_count(slug: str) -> int:
        with get_db() as db:
            problem = db.query(ProblemDB).filter_by(slug=slug).first()
            if problem:
                problem.retry_count = (problem.retry_count or 0) + 1
                db.commit()
                return problem.retry_count
            return 0

    @staticmethod
    def reset_problem(slug: str) -> bool:
        with get_db() as db:
            problem = db.query(ProblemDB).filter_by(slug=slug).first()
            if problem:
                problem.status = ProblemStatus.PENDING.value
                problem.retry_count = 0
                problem.updated_at = datetime.utcnow()
                db.commit()
                return True
            return False

    @staticmethod
    def record_generation_attempt(
        problem_slug: str,
        attempt_number: int,
        prompt: str,
        response_code: Optional[str],
        is_valid_python: bool,
        duration_seconds: float,
        model_name: str,
        error_message: Optional[str] = None,
    ) -> GenerationAttemptDB:
        with get_db() as db:
            attempt = GenerationAttemptDB(
                problem_slug=problem_slug,
                attempt_number=attempt_number,
                prompt=prompt,
                response_code=response_code,
                is_valid_python=is_valid_python,
                duration_seconds=duration_seconds,
                model_name=model_name,
                error_message=error_message,
            )
            db.add(attempt)
            db.commit()
            db.refresh(attempt)
            return attempt

    @staticmethod
    def record_test_run(
        problem_slug: str,
        attempt_id: Optional[int],
        passed: bool,
        total_tests: int,
        passed_tests: int,
        failed_tests: int,
        diagnostics: Optional[dict] = None,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        duration_ms: float = 0.0,
    ) -> LocalTestRunDB:
        with get_db() as db:
            test_run = LocalTestRunDB(
                problem_slug=problem_slug,
                attempt_id=attempt_id,
                passed=passed,
                total_tests=total_tests,
                passed_tests=passed_tests,
                failed_tests=failed_tests,
                diagnostics_json=json.dumps(diagnostics) if diagnostics else None,
                stdout=stdout,
                stderr=stderr,
                duration_ms=duration_ms,
            )
            db.add(test_run)
            db.commit()
            db.refresh(test_run)
            return test_run

    @staticmethod
    def record_submission(
        problem_slug: str,
        attempt_id: Optional[int],
        submission_id: Optional[str],
        verdict: Verdict,
        runtime_ms: Optional[int] = None,
        memory_mb: Optional[float] = None,
        raw_verdict_text: Optional[str] = None,
    ) -> SubmissionDB:
        with get_db() as db:
            sub = SubmissionDB(
                problem_slug=problem_slug,
                attempt_id=attempt_id,
                submission_id=submission_id,
                verdict=verdict.value,
                runtime_ms=runtime_ms,
                memory_mb=memory_mb,
                raw_verdict_text=raw_verdict_text,
            )
            db.add(sub)
            db.commit()
            db.refresh(sub)
            return sub

    @staticmethod
    def record_account_verification(
        username: Optional[str],
        expected_username: str,
        status: VerificationStatus,
        details: Optional[str] = None,
    ) -> AccountVerificationDB:
        with get_db() as db:
            verification = AccountVerificationDB(
                username=username,
                expected_username=expected_username,
                status=status.value,
                details=details,
                verified_at=datetime.utcnow(),
            )
            db.add(verification)
            db.commit()
            db.refresh(verification)
            return verification

    @staticmethod
    def get_latest_account_verification() -> Optional[AccountVerificationDB]:
        with get_db() as db:
            return (
                db.query(AccountVerificationDB)
                .order_by(AccountVerificationDB.verified_at.desc())
                .first()
            )
