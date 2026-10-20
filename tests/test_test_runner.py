import os
from app.test_runner import TestRunner

def test_successful_local_execution():
    """Test running a correct solution in an isolated subprocess."""
    runner = TestRunner(timeout_seconds=5)
    code = """
class Solution:
    def add(self, a: int, b: int) -> int:
        return a + b
"""
    test_cases = [
        {"args": [1, 2], "expected": 3},
        {"args": [-1, 1], "expected": 0},
    ]
    result = runner.run_tests(
        code=code,
        class_name="Solution",
        method_name="add",
        test_cases=test_cases,
    )
    assert result.passed is True
    assert result.passed_tests == 2
    assert result.failed_tests == 0

def test_failing_local_execution():
    """Test detecting wrong output in an isolated subprocess."""
    runner = TestRunner(timeout_seconds=5)
    code = """
class Solution:
    def add(self, a: int, b: int) -> int:
        return a - b  # Buggy implementation
"""
    test_cases = [
        {"args": [5, 2], "expected": 7},
    ]
    result = runner.run_tests(
        code=code,
        class_name="Solution",
        method_name="add",
        test_cases=test_cases,
    )
    assert result.passed is False
    assert result.failed_tests == 1
    assert len(result.failures) == 1
    assert result.failures[0]["actual"] == 3

def test_timeout_handling():
    """Test that infinite loops or long-running solutions are killed after timeout."""
    runner = TestRunner(timeout_seconds=2)
    code = """
class Solution:
    def infinite(self, x: int) -> int:
        while True:
            pass
        return x
"""
    test_cases = [{"args": [1], "expected": 1}]
    result = runner.run_tests(
        code=code,
        class_name="Solution",
        method_name="infinite",
        test_cases=test_cases,
    )
    assert result.passed is False
    assert any("timed out" in f.get("error", "").lower() for f in result.failures)

def test_environment_sanitization():
    """Test that runner removes sensitive environment variables."""
    os.environ["SECRET_TOKEN_XYZ"] = "supersecret123"
    runner = TestRunner()
    clean_env = runner._sanitize_env()
    assert "SECRET_TOKEN_XYZ" not in clean_env
    del os.environ["SECRET_TOKEN_XYZ"]
