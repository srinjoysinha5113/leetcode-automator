import json
from typing import Any, Dict, List, Optional, Tuple
from app.config import logger, settings
from app.database import DatabaseManager
from app.llm_client import OllamaClient
from app.models import GenerationResult, TestResult
from app.test_runner import TestRunner

REPAIR_PROMPT_TEMPLATE = """The previous Python solution for '{title}' failed validation or testing.

PROBLEM STATEMENT:
{statement}

PREVIOUS CODE:
```python
{code}
```

FAILURE DIAGNOSTICS:
{diagnostics}

REQUIREMENTS:
1. Fix the bug(s) identified above.
2. Keep the exact class `{class_name}` and method `{method_name}`.
3. Provide the COMPLETE repaired Python 3 solution, including any helper functions or imports.
4. Return ONLY the code inside a ```python ... ``` block without conversational filler.
"""

class RepairLoop:
    """Orchestrates iterative code debugging and repair with Ollama."""

    def __init__(
        self,
        llm_client: Optional[OllamaClient] = None,
        test_runner: Optional[TestRunner] = None,
        max_attempts: Optional[int] = None,
    ):
        self.llm_client = llm_client or OllamaClient()
        self.test_runner = test_runner or TestRunner()
        self.max_attempts = max_attempts or settings.MAX_REPAIR_ATTEMPTS

    def _format_diagnostics(self, test_result: TestResult, syntax_error: Optional[str] = None) -> str:
        lines = []
        if syntax_error:
            lines.append(f"SYNTAX / VALIDATION ERROR:\n{syntax_error}")
        if test_result.stderr:
            lines.append(f"STDERR / RUNTIME TRACEBACK:\n{test_result.stderr.strip()}")
        if test_result.failures:
            lines.append("FAILING TEST CASES:")
            for f in test_result.failures[:3]:  # Top 3 failures for conciseness
                lines.append(f"- Input: {f.get('input')}")
                lines.append(f"  Expected: {f.get('expected')}")
                lines.append(f"  Actual: {f.get('actual')}")
                if f.get("error"):
                    lines.append(f"  Error: {f.get('error')}")
        return "\n".join(lines) if lines else "Solution failed local validation tests."

    def repair(
        self,
        problem_slug: str,
        title: str,
        statement: str,
        class_name: str,
        method_name: Optional[str],
        current_code: str,
        initial_test_result: Optional[TestResult],
        initial_error: Optional[str],
        test_cases: List[Dict[str, Any]],
        start_attempt_number: int = 1,
    ) -> Tuple[bool, str, Optional[TestResult]]:
        """
        Iteratively prompts the LLM to fix failing code until all tests pass
        or the maximum retry attempts are exhausted.
        """
        code = current_code
        test_result = initial_test_result
        current_error = initial_error

        for attempt in range(start_attempt_number, self.max_attempts + 1):
            logger.info(f"[{problem_slug}] Repair attempt {attempt}/{self.max_attempts}...")

            diagnostics = self._format_diagnostics(
                test_result=test_result or TestResult(passed=False),
                syntax_error=current_error
            )

            prompt = REPAIR_PROMPT_TEMPLATE.format(
                title=title,
                statement=statement or "Solve the problem correctly.",
                code=code,
                diagnostics=diagnostics,
                class_name=class_name,
                method_name=method_name or "solve",
            )

            gen_result: GenerationResult = self.llm_client.generate(
                prompt=prompt,
                expected_class=class_name,
                expected_method=method_name,
            )

            # Record attempt in database
            db_attempt = DatabaseManager.record_generation_attempt(
                problem_slug=problem_slug,
                attempt_number=attempt,
                prompt=prompt,
                response_code=gen_result.code,
                is_valid_python=gen_result.is_valid_python,
                duration_seconds=gen_result.duration_seconds,
                model_name=gen_result.model,
                error_message=gen_result.error,
            )

            if not gen_result.is_valid_python:
                code = gen_result.code or code
                current_error = gen_result.error
                continue

            code = gen_result.code
            current_error = None

            # Run tests on repaired code
            test_result = self.test_runner.run_tests(
                code=code,
                class_name=class_name,
                method_name=method_name,
                test_cases=test_cases,
            )

            # Record test run in database
            DatabaseManager.record_test_run(
                problem_slug=problem_slug,
                attempt_id=db_attempt.id,
                passed=test_result.passed,
                total_tests=test_result.total_tests,
                passed_tests=test_result.passed_tests,
                failed_tests=test_result.failed_tests,
                diagnostics={"failures": test_result.failures},
                stdout=test_result.stdout,
                stderr=test_result.stderr,
                duration_ms=test_result.duration_ms,
            )

            if test_result.passed:
                logger.info(f"[{problem_slug}] Repair succeeded on attempt {attempt}!")
                return True, code, test_result

        logger.warning(f"[{problem_slug}] Repair loop exhausted ({self.max_attempts} attempts).")
        return False, code, test_result
