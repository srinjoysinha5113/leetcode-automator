import pytest
from unittest.mock import AsyncMock, MagicMock
from app.database import DatabaseManager, init_db
from app.models import GenerationResult, ProblemDB, ProblemStatus, TestResult
from app.orchestrator import PipelineOrchestrator

@pytest.fixture
def mock_pipeline():
    init_db()
    llm = MagicMock()
    llm.check_health.return_value = (True, "OK")
    llm.model = "llama3.2:3b"

    runner = MagicMock()
    submitter = MagicMock()
    submitter.submit_solution = AsyncMock()
    verifier = MagicMock()
    verifier.verify_identity = AsyncMock()

    orchestrator = PipelineOrchestrator(
        llm_client=llm,
        test_runner=runner,
        submitter=submitter,
        verifier=verifier,
    )
    return orchestrator

@pytest.mark.asyncio
async def test_dry_run_never_submits(mock_pipeline):
    """Test that dry-run mode executes local testing but strictly never invokes the submitter."""
    slug = "test-dry-run-problem"
    DatabaseManager.upsert_problem(
        slug=slug,
        title="Test Dry Run Problem",
        url="http://test",
        category="Arrays",
        difficulty="Easy",
        statement="Solve this",
        starter_code="class Solution:\n    def solve(self): pass",
        class_name="Solution",
        method_name="solve",
    )
    problem = DatabaseManager.get_problem(slug)

    # Configure mock LLM to return valid code
    mock_pipeline.llm_client.generate.return_value = GenerationResult(
        code="class Solution:\n    def solve(self): return True",
        is_valid_python=True,
        has_target_class=True,
        has_target_method=True,
        model="llama3.2:3b",
    )
    # Configure runner to report passing tests
    mock_pipeline.test_runner.run_tests.return_value = TestResult(
        passed=True,
        total_tests=1,
        passed_tests=1,
    )

    success = await mock_pipeline.process_problem(problem, dry_run=True)
    assert success is True

    # Critical check: Submitter was NEVER called
    mock_pipeline.submitter.submit_solution.assert_not_called()

    # Database status should be LOCAL_TEST_PASSED, not ACCEPTED or SUBMITTING
    updated = DatabaseManager.get_problem(slug)
    assert updated.status == ProblemStatus.LOCAL_TEST_PASSED.value
