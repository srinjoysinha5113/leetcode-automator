import enum
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class ProblemStatus(str, enum.Enum):
    PENDING = "PENDING"
    FETCHED = "FETCHED"
    GENERATING = "GENERATING"
    LOCAL_TEST_PASSED = "LOCAL_TEST_PASSED"
    LOCAL_TEST_FAILED = "LOCAL_TEST_FAILED"
    SUBMITTING = "SUBMITTING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"

class Verdict(str, enum.Enum):
    ACCEPTED = "Accepted"
    WRONG_ANSWER = "Wrong Answer"
    TIME_LIMIT_EXCEEDED = "Time Limit Exceeded"
    RUNTIME_ERROR = "Runtime Error"
    COMPILE_ERROR = "Compile Error"
    MEMORY_LIMIT_EXCEEDED = "Memory Limit Exceeded"
    PENDING = "Pending"
    UNKNOWN = "Unknown"

class VerificationStatus(str, enum.Enum):
    VERIFIED = "VERIFIED"
    MISMATCH = "MISMATCH"
    NOT_LOGGED_IN = "NOT_LOGGED_IN"
    UNVERIFIABLE = "UNVERIFIABLE"

# SQLAlchemy Models
class ProblemDB(Base):
    __tablename__ = "problems"

    slug = Column(String(128), primary_key=True)
    title = Column(String(256), nullable=False)
    url = Column(String(512), nullable=False)
    category = Column(String(128), nullable=False)
    difficulty = Column(String(32), nullable=False)
    order_index = Column(Integer, default=0)
    status = Column(String(32), default=ProblemStatus.PENDING.value, index=True)
    statement = Column(Text, nullable=True)
    starter_code = Column(Text, nullable=True)
    method_name = Column(String(128), nullable=True)
    class_name = Column(String(128), default="Solution")
    sample_test_case = Column(Text, nullable=True)
    example_testcases = Column(Text, nullable=True)  # JSON encoded list
    solution_code_path = Column(String(512), nullable=True)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    attempts = relationship("GenerationAttemptDB", back_populates="problem", cascade="all, delete-orphan")
    test_runs = relationship("LocalTestRunDB", back_populates="problem", cascade="all, delete-orphan")
    submissions = relationship("SubmissionDB", back_populates="problem", cascade="all, delete-orphan")

class GenerationAttemptDB(Base):
    __tablename__ = "generation_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    problem_slug = Column(String(128), ForeignKey("problems.slug"), nullable=False, index=True)
    attempt_number = Column(Integer, nullable=False)
    prompt = Column(Text, nullable=False)
    response_code = Column(Text, nullable=True)
    is_valid_python = Column(Boolean, default=False)
    duration_seconds = Column(Float, default=0.0)
    model_name = Column(String(64), nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    problem = relationship("ProblemDB", back_populates="attempts")
    test_runs = relationship("LocalTestRunDB", back_populates="attempt")

class LocalTestRunDB(Base):
    __tablename__ = "local_test_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    problem_slug = Column(String(128), ForeignKey("problems.slug"), nullable=False, index=True)
    attempt_id = Column(Integer, ForeignKey("generation_attempts.id"), nullable=True, index=True)
    passed = Column(Boolean, default=False)
    total_tests = Column(Integer, default=0)
    passed_tests = Column(Integer, default=0)
    failed_tests = Column(Integer, default=0)
    diagnostics_json = Column(Text, nullable=True)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    duration_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    problem = relationship("ProblemDB", back_populates="test_runs")
    attempt = relationship("GenerationAttemptDB", back_populates="test_runs")

class SubmissionDB(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    problem_slug = Column(String(128), ForeignKey("problems.slug"), nullable=False, index=True)
    attempt_id = Column(Integer, ForeignKey("generation_attempts.id"), nullable=True)
    submission_id = Column(String(64), nullable=True, index=True)
    verdict = Column(String(64), default=Verdict.UNKNOWN.value, index=True)
    runtime_ms = Column(Integer, nullable=True)
    memory_mb = Column(Float, nullable=True)
    raw_verdict_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    problem = relationship("ProblemDB", back_populates="submissions")

class AccountVerificationDB(Base):
    __tablename__ = "account_verifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(128), nullable=True)
    expected_username = Column(String(128), nullable=False)
    status = Column(String(64), nullable=False)
    details = Column(Text, nullable=True)
    verified_at = Column(DateTime, default=datetime.utcnow)

class ApplicationRunDB(Base):
    __tablename__ = "application_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    command = Column(String(64), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    status = Column(String(32), default="RUNNING")
    problems_processed = Column(Integer, default=0)
    notes = Column(Text, nullable=True)

# Pydantic Schemas
class TestCase(BaseModel):
    input_args: List[Any] = Field(default_factory=list)
    input_kwargs: Dict[str, Any] = Field(default_factory=dict)
    expected: Any = None
    description: str = ""

class TestResult(BaseModel):
    __test__ = False
    passed: bool
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    failures: List[Dict[str, Any]] = Field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    duration_ms: float = 0.0


class GenerationResult(BaseModel):
    code: str
    is_valid_python: bool
    has_target_class: bool
    has_target_method: bool
    error: Optional[str] = None
    duration_seconds: float = 0.0
    model: str = ""

class SubmissionResult(BaseModel):
    submission_id: Optional[str] = None
    verdict: Verdict = Verdict.UNKNOWN
    runtime_ms: Optional[int] = None
    memory_mb: Optional[float] = None
    raw_output: str = ""
    error: Optional[str] = None
