import pytest
from app.database import get_db, init_db
from app.models import GenerationAttemptDB, LocalTestRunDB, ProblemDB, ProblemStatus, SubmissionDB
from app.problem_queue import ProblemQueue

@pytest.fixture(autouse=True)
def setup_test_queue():
    init_db()
    with get_db() as db:
        db.query(LocalTestRunDB).delete()
        db.query(GenerationAttemptDB).delete()
        db.query(SubmissionDB).delete()
        db.query(ProblemDB).delete()
        # Seed test problems
        p1 = ProblemDB(slug="prob-1", title="Problem 1", url="url1", category="Cat", difficulty="Easy", order_index=1, status=ProblemStatus.PENDING.value)
        p2 = ProblemDB(slug="prob-2", title="Problem 2", url="url2", category="Cat", difficulty="Medium", order_index=2, status=ProblemStatus.ACCEPTED.value)
        p3 = ProblemDB(slug="prob-3", title="Problem 3", url="url3", category="Cat", difficulty="Hard", order_index=3, status=ProblemStatus.LOCAL_TEST_FAILED.value)
        db.add_all([p1, p2, p3])
        db.commit()


def test_problem_queue_ordering():
    """Test that problems are returned in ascending order_index."""
    queued = ProblemQueue.get_queued_problems(limit=10)
    indices = [p.order_index for p in queued]
    assert indices == sorted(indices)

def test_duplicate_submission_prevention():
    """Test that ACCEPTED problems are strictly excluded from execution queue."""
    queued = ProblemQueue.get_queued_problems(limit=10)
    slugs = [p.slug for p in queued]
    assert "prob-2" not in slugs  # prob-2 is already ACCEPTED
    assert "prob-1" in slugs

def test_resume_after_interruption():
    """Test that restarting the queue picks up remaining non-accepted problems."""
    # When restarting with limit 1, it should fetch prob-1
    batch = ProblemQueue.get_queued_problems(limit=1)
    assert len(batch) == 1
    assert batch[0].slug == "prob-1"

def test_reset_for_retry():
    """Test resetting a problem back to PENDING."""
    success = ProblemQueue.reset_for_retry("prob-3")
    assert success is True
    prob = ProblemQueue.get_problem_by_slug("prob-3")
    assert prob.status == ProblemStatus.PENDING.value
    assert prob.retry_count == 0
