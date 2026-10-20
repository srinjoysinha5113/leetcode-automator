import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.account_verifier import AccountVerifier
from app.config import logger, settings
from app.database import DatabaseManager
from app.llm_client import OllamaClient
from app.models import (
    GenerationResult,
    ProblemDB,
    ProblemStatus,
    SubmissionResult,
    TestResult,
    Verdict,
    VerificationStatus,
)
from app.problem_queue import ProblemQueue
from app.problem_source import ProblemSource
from app.repair_loop import RepairLoop
from app.solution_generator import SolutionGenerator
from app.submitter import LeetCodeSubmitter
from app.test_runner import TestRunner

class PipelineOrchestrator:
    """End-to-end pipeline coordinator for problem solving, testing, repairing, and submitting."""

    def __init__(
        self,
        llm_client: Optional[OllamaClient] = None,
        test_runner: Optional[TestRunner] = None,
        repair_loop: Optional[RepairLoop] = None,
        problem_source: Optional[ProblemSource] = None,
        submitter: Optional[LeetCodeSubmitter] = None,
        verifier: Optional[AccountVerifier] = None,
    ):
        self.llm_client = llm_client or OllamaClient()
        self.test_runner = test_runner or TestRunner()
        self.repair_loop = repair_loop or RepairLoop(self.llm_client, self.test_runner)
        self.problem_source = problem_source or ProblemSource()
        self.submitter = submitter or LeetCodeSubmitter()
        self.verifier = verifier or AccountVerifier()

    def _parse_example_test_cases(self, problem: ProblemDB, details: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Extracts structured test cases from problem metadata or defaults."""
        test_cases: List[Dict[str, Any]] = []

        # 1. From details or problem db
        raw_examples = None
        if details and details.get("example_testcases"):
            raw_examples = details["example_testcases"]
        elif problem.example_testcases:
            try:
                raw_examples = json.loads(problem.example_testcases)
            except Exception:
                pass

        if raw_examples and isinstance(raw_examples, list):
            for item in raw_examples:
                # Raw example lines in LeetCode are often newline-separated input arguments
                lines = [line.strip() for line in str(item).split("\n") if line.strip()]
                parsed_args = []
                for line in lines:
                    try:
                        parsed_args.append(json.loads(line))
                    except Exception:
                        parsed_args.append(line)
                test_cases.append({"args": parsed_args, "expected": None})

        # 2. Known built-in test case fixtures for common initial NeetCode problems
        known_fixtures = {
            "two-sum": [
                {"args": [[2, 7, 11, 15], 9], "expected": [0, 1]},
                {"args": [[3, 2, 4], 6], "expected": [1, 2]},
                {"args": [[3, 3], 6], "expected": [0, 1]},
            ],
            "contains-duplicate": [
                {"args": [[1, 2, 3, 1]], "expected": True},
                {"args": [[1, 2, 3, 4]], "expected": False},
                {"args": [[1, 1, 1, 3, 3, 4, 3, 2, 4, 2]], "expected": True},
            ],
            "valid-anagram": [
                {"args": ["anagram", "nagaram"], "expected": True},
                {"args": ["rat", "car"], "expected": False},
            ],
            "valid-palindrome": [
                {"args": ["A man, a plan, a canal: Panama"], "expected": True},
                {"args": ["race a car"], "expected": False},
                {"args": [" "], "expected": True},
            ],
            "binary-search": [
                {"args": [[-1, 0, 3, 5, 9, 12], 9], "expected": 4},
                {"args": [[-1, 0, 3, 5, 9, 12], 2], "expected": -1},
            ],
            "reverse-linked-list": [
                {"args": [[1, 2, 3, 4, 5]], "expected": [5, 4, 3, 2, 1]},
                {"args": [[1, 2]], "expected": [2, 1]},
                {"args": [[]], "expected": []},
            ],
            "invert-binary-tree": [
                {"args": [[4, 2, 7, 1, 3, 6, 9]], "expected": [4, 7, 2, 9, 6, 3, 1]},
                {"args": [[2, 1, 3]], "expected": [2, 3, 1]},
                {"args": [[]], "expected": []},
            ],
            "min-stack": [
                {
                    "args": [
                        ["MinStack", "push", "push", "push", "getMin", "pop", "top", "getMin"],
                        [[], [-2], [0], [-3], [], [], [], []]
                    ],
                    "expected": [None, None, None, None, -3, None, 0, -2]
                }
            ],
        }

        if problem.slug in known_fixtures:
            return known_fixtures[problem.slug]

        return test_cases

    async def process_problem(
        self,
        problem: ProblemDB,
        dry_run: bool = False,
    ) -> bool:
        """Processes a single problem through ingestion, generation, testing, repair, and submission."""
        slug = problem.slug
        logger.info(f"==> Processing problem [{problem.order_index}]: {problem.title} ({slug})")

        # 1. Ensure problem details and starter code are fetched
        details = None
        if not problem.statement or not problem.starter_code:
            logger.info(f"[{slug}] Fetching problem statement and starter code...")
            details = self.problem_source.fetch_problem_details(slug)
            if details:
                DatabaseManager.upsert_problem(
                    slug=slug,
                    title=problem.title,
                    url=problem.url,
                    category=problem.category,
                    difficulty=problem.difficulty,
                    order_index=problem.order_index,
                    class_name=details.get("class_name", problem.class_name),
                    method_name=details.get("method_name", problem.method_name),
                    statement=details.get("statement"),
                    starter_code=details.get("starter_code"),
                    sample_test_case=details.get("sample_test_case"),
                    example_testcases=details.get("example_testcases"),
                )
                # Refresh problem instance
                problem = DatabaseManager.get_problem(slug)

        test_cases = self._parse_example_test_cases(problem, details)

        # 2. Generate initial solution
        DatabaseManager.update_problem_status(slug, ProblemStatus.GENERATING)
        gen = SolutionGenerator(self.llm_client)
        gen_res: GenerationResult = gen.generate_solution(
            title=problem.title,
            category=problem.category,
            difficulty=problem.difficulty,
            statement=problem.statement or "Solve the problem efficiently.",
            starter_code=problem.starter_code,
            class_name=problem.class_name or "Solution",
            method_name=problem.method_name,
        )

        db_attempt = DatabaseManager.record_generation_attempt(
            problem_slug=slug,
            attempt_number=1,
            prompt="Initial generation prompt",
            response_code=gen_res.code,
            is_valid_python=gen_res.is_valid_python,
            duration_seconds=gen_res.duration_seconds,
            model_name=gen_res.model,
            error_message=gen_res.error,
        )

        current_code = gen_res.code
        test_passed = False
        test_result: Optional[TestResult] = None

        if gen_res.is_valid_python:
            # 3. Run isolated tests
            test_result = self.test_runner.run_tests(
                code=current_code,
                class_name=problem.class_name or "Solution",
                method_name=problem.method_name,
                test_cases=test_cases,
            )

            DatabaseManager.record_test_run(
                problem_slug=slug,
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
            test_passed = test_result.passed

        # 4. Trigger repair loop if tests or syntax validation failed
        if not test_passed:
            logger.info(f"[{slug}] Initial solution did not pass. Entering repair loop...")
            success, repaired_code, repaired_test_result = self.repair_loop.repair(
                problem_slug=slug,
                title=problem.title,
                statement=problem.statement or "",
                class_name=problem.class_name or "Solution",
                method_name=problem.method_name,
                current_code=current_code,
                initial_test_result=test_result,
                initial_error=gen_res.error,
                test_cases=test_cases,
                start_attempt_number=2,
            )
            if success:
                test_passed = True
                current_code = repaired_code
                test_result = repaired_test_result
            else:
                logger.warning(f"[{slug}] Could not repair solution within configured limit.")
                DatabaseManager.update_problem_status(slug, ProblemStatus.LOCAL_TEST_FAILED)
                return False

        # 5. Save verified solution file
        solution_file = settings.SOLUTIONS_DIR / f"{slug}.py"
        with open(solution_file, "w", encoding="utf-8") as sf:
            sf.write(current_code)

        DatabaseManager.update_problem_status(
            slug,
            ProblemStatus.LOCAL_TEST_PASSED,
            solution_path=str(solution_file)
        )
        logger.info(f"[{slug}] Local tests passed! Solution saved to {solution_file}")

        # 6. Submission stage
        if dry_run or not settings.AUTO_SUBMIT:
            mode_desc = "DRY-RUN" if dry_run else "AUTO_SUBMIT=false"
            logger.info(f"[{slug}] {mode_desc}: Submission skipped. Problem remains in LOCAL_TEST_PASSED state.")
            return True

        # Live Submission to LeetCode
        DatabaseManager.update_problem_status(slug, ProblemStatus.SUBMITTING)
        logger.info(f"[{slug}] Starting live LeetCode submission...")

        sub_result: SubmissionResult = await self.submitter.submit_solution(
            problem_slug=slug,
            solution_code=current_code,
            attempt_id=db_attempt.id,
        )

        if sub_result.verdict == Verdict.ACCEPTED:
            logger.info(f"[{slug}] >>> SUBMISSION ACCEPTED! <<< (Runtime: {sub_result.runtime_ms} ms)")
            DatabaseManager.update_problem_status(slug, ProblemStatus.ACCEPTED)
            return True
        else:
            logger.warning(f"[{slug}] Submission rejected: {sub_result.verdict.value}. Details: {sub_result.error or sub_result.raw_output}")
            retry_count = DatabaseManager.increment_retry_count(slug)
            if retry_count < settings.MAX_SUBMISSIONS_PER_PROBLEM:
                DatabaseManager.update_problem_status(slug, ProblemStatus.LOCAL_TEST_FAILED)
            else:
                DatabaseManager.update_problem_status(slug, ProblemStatus.REJECTED)
            return False

    async def run(
        self,
        limit: Optional[int] = None,
        slug: Optional[str] = None,
        dry_run: bool = False,
        all_problems: bool = False,
    ) -> None:
        """Executes the pipeline for queued problems."""
        # Preflight health check
        healthy, msg = self.llm_client.check_health()
        if not healthy:
            logger.error(f"Preflight Check Failed: {msg}")
            return

        if not dry_run and settings.AUTO_SUBMIT:
            # Verify account identity before starting real submissions
            v_status, username, v_msg = await self.verifier.verify_identity(headless=True)
            if v_status != VerificationStatus.VERIFIED:
                logger.error(f"Account Verification Failed: {v_msg}. Cannot proceed with submission mode.")
                return

        effective_limit = None if all_problems else (limit or 1)
        problems = ProblemQueue.get_queued_problems(limit=effective_limit, slug=slug)

        if not problems:
            logger.info("No queued problems found to process.")
            return

        logger.info(f"Starting batch run for {len(problems)} problem(s) (dry_run={dry_run})...")
        processed = 0
        accepted = 0

        for prob in problems:
            success = await self.process_problem(prob, dry_run=dry_run)
            processed += 1
            if success:
                accepted += 1

        logger.info(f"Batch completed: {processed} processed, {accepted} succeeded.")
