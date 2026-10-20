import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import (
    Base,
    ProblemDB,
    ProblemStatus,
    GenerationAttemptDB,
    LocalTestRunDB,
    SubmissionDB,
    Verdict,
    AccountVerificationDB,
    VerificationStatus,
)

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_database_creation_and_tables(test_db):
    """Test that all required tables are properly created."""
    tables = Base.metadata.tables.keys()
    assert "problems" in tables
    assert "generation_attempts" in tables
    assert "local_test_runs" in tables
    assert "submissions" in tables
    assert "account_verifications" in tables
    assert "application_runs" in tables

def test_duplicate_problem_prevention(test_db):
    """Test unique constraint on problem slug prevents duplicate entries."""
    prob1 = ProblemDB(
        slug="two-sum",
        title="Two Sum",
        url="https://leetcode.com/problems/two-sum/",
        category="Arrays & Hashing",
        difficulty="Easy",
        order_index=1,
    )
    test_db.add(prob1)
    test_db.commit()

    # Attempting to add same slug should raise IntegrityError
    prob2 = ProblemDB(
        slug="two-sum",
        title="Two Sum Duplicate",
        url="https://leetcode.com/problems/two-sum/",
        category="Arrays & Hashing",
        difficulty="Easy",
        order_index=2,
    )
    test_db.add(prob2)
    with pytest.raises(Exception):
        test_db.commit()
    test_db.rollback()

def test_submission_state_transitions(test_db):
    """Test explicit lifecycle transitions for a problem."""
    prob = ProblemDB(
        slug="valid-anagram",
        title="Valid Anagram",
        url="https://leetcode.com/problems/valid-anagram/",
        category="Arrays & Hashing",
        difficulty="Easy",
        status=ProblemStatus.PENDING.value,
    )
    test_db.add(prob)
    test_db.commit()

    # PENDING -> GENERATING
    prob.status = ProblemStatus.GENERATING.value
    test_db.commit()
    assert prob.status == ProblemStatus.GENERATING.value

    # GENERATING -> LOCAL_TEST_PASSED
    prob.status = ProblemStatus.LOCAL_TEST_PASSED.value
    prob.solution_code_path = "data/solutions/valid-anagram.py"
    test_db.commit()
    assert prob.status == ProblemStatus.LOCAL_TEST_PASSED.value
    assert prob.solution_code_path == "data/solutions/valid-anagram.py"

    # LOCAL_TEST_PASSED -> SUBMITTING
    prob.status = ProblemStatus.SUBMITTING.value
    test_db.commit()
    assert prob.status == ProblemStatus.SUBMITTING.value

    # SUBMITTING -> ACCEPTED
    prob.status = ProblemStatus.ACCEPTED.value
    test_db.commit()
    assert prob.status == ProblemStatus.ACCEPTED.value

def test_account_verification_recording(test_db):
    """Test recording account verification events."""
    verif = AccountVerificationDB(
        username="srinjoy",
        expected_username="srinjoy",
        status=VerificationStatus.VERIFIED.value,
        details="Match verified",
    )
    test_db.add(verif)
    test_db.commit()
    assert verif.id is not None
    assert verif.status == "VERIFIED"
