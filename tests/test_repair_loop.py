from unittest.mock import MagicMock
from app.database import DatabaseManager, init_db
from app.models import GenerationResult, TestResult
from app.repair_loop import RepairLoop

def test_repair_loop_limits():
    """Test that repair loop stops when max_attempts is reached."""
    init_db()
    DatabaseManager.upsert_problem(
        slug="test-slug",
        title="Test Problem",
        url="http://test",
        category="Cat",
        difficulty="Easy"
    )
    mock_llm = MagicMock()
    mock_runner = MagicMock()


    # Always return failing test result
    mock_llm.generate.return_value = GenerationResult(
        code="class Solution:\n    def solve(self): return False",
        is_valid_python=True,
        has_target_class=True,
        has_target_method=True,
        model="mock",
    )
    mock_runner.run_tests.return_value = TestResult(
        passed=False,
        total_tests=1,
        failed_tests=1,
        failures=[{"error": "Wrong answer"}]
    )

    loop = RepairLoop(llm_client=mock_llm, test_runner=mock_runner, max_attempts=3)
    success, final_code, test_res = loop.repair(
        problem_slug="test-slug",
        title="Test Problem",
        statement="Solve it",
        class_name="Solution",
        method_name="solve",
        current_code="class Solution: pass",
        initial_test_result=None,
        initial_error="Initial failure",
        test_cases=[{"args": [], "expected": True}],
        start_attempt_number=1,
    )

    assert success is False
    # Verified max_attempts=3 was respected
    assert mock_llm.generate.call_count == 3

def test_repair_loop_success_on_retry():
    """Test repair loop terminates early when a repair succeeds."""
    init_db()
    DatabaseManager.upsert_problem(
        slug="test-slug-2",
        title="Test Problem 2",
        url="http://test2",
        category="Cat",
        difficulty="Easy"
    )
    mock_llm = MagicMock()
    mock_runner = MagicMock()


    mock_llm.generate.return_value = GenerationResult(
        code="class Solution:\n    def solve(self): return True",
        is_valid_python=True,
        has_target_class=True,
        has_target_method=True,
        model="mock",
    )
    # Succeeds on first repair call
    mock_runner.run_tests.return_value = TestResult(
        passed=True,
        total_tests=1,
        passed_tests=1,
    )

    loop = RepairLoop(llm_client=mock_llm, test_runner=mock_runner, max_attempts=3)
    success, final_code, test_res = loop.repair(
        problem_slug="test-slug-2",
        title="Test Problem",
        statement="Solve it",
        class_name="Solution",
        method_name="solve",
        current_code="class Solution: pass",
        initial_test_result=None,
        initial_error="Initial failure",
        test_cases=[{"args": [], "expected": True}],
        start_attempt_number=1,
    )

    assert success is True
    assert mock_llm.generate.call_count == 1
