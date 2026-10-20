import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.config import logger, settings
from app.models import TestCase, TestResult

HARNESS_TEMPLATE = """# -*- coding: utf-8 -*-
# Auto-generated isolated test harness
import sys
import json
import math
import collections
import heapq
import bisect
import re
from typing import *

# JSON Compatibility
true = True
false = False
null = None

# Security: Adjust recursion limit to avoid stack overflow crashes
sys.setrecursionlimit(2500)

# Data Structures
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
    def __repr__(self):
        return f"ListNode({self.val})"

def build_linked_list(values):
    if not values:
        return None
    dummy = ListNode(0)
    curr = dummy
    for v in values:
        curr.next = ListNode(v)
        curr = curr.next
    return dummy.next

def linked_list_to_list(head, max_nodes=10000):
    result = []
    visited = set()
    curr = head
    count = 0
    while curr and count < max_nodes:
        if id(curr) in visited:
            result.append(f"[Cycle to {curr.val}]")
            break
        visited.add(id(curr))
        result.append(curr.val)
        curr = curr.next
        count += 1
    return result

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
    def __repr__(self):
        return f"TreeNode({self.val})"

def build_tree(values):
    if not values or values[0] is None:
        return None
    root = TreeNode(values[0])
    queue = [root]
    i = 1
    n = len(values)
    while queue and i < n:
        node = queue.pop(0)
        if i < n and values[i] is not None:
            node.left = TreeNode(values[i])
            queue.append(node.left)
        i += 1
        if i < n and values[i] is not None:
            node.right = TreeNode(values[i])
            queue.append(node.right)
        i += 1
    return root

def tree_to_list(root):
    if not root:
        return []
    result = []
    queue = [root]
    while queue:
        node = queue.pop(0)
        if node:
            result.append(node.val)
            queue.append(node.left)
            queue.append(node.right)
        else:
            result.append(None)
    while result and result[-1] is None:
        result.pop()
    return result

def deep_equal(actual, expected):
    if isinstance(actual, ListNode):
        actual = linked_list_to_list(actual)
    if isinstance(expected, ListNode):
        expected = linked_list_to_list(expected)
    if isinstance(actual, TreeNode):
        actual = tree_to_list(actual)
    if isinstance(expected, TreeNode):
        expected = tree_to_list(expected)

    if isinstance(actual, float) and isinstance(expected, (int, float)):
        return math.isclose(actual, float(expected), rel_tol=1e-5, abs_tol=1e-5)
    if isinstance(expected, float) and isinstance(actual, (int, float)):
        return math.isclose(float(actual), expected, rel_tol=1e-5, abs_tol=1e-5)

    if isinstance(actual, (list, tuple)) and isinstance(expected, (list, tuple)):
        if len(actual) != len(expected):
            return False
        if all(deep_equal(a, e) for a, e in zip(actual, expected)):
            return True
        try:
            norm_actual = sorted([sorted(x) if isinstance(x, (list, tuple)) else x for x in actual], key=lambda x: str(x))
            norm_expected = sorted([sorted(x) if isinstance(x, (list, tuple)) else x for x in expected], key=lambda x: str(x))
            return all(deep_equal(a, e) for a, e in zip(norm_actual, norm_expected))
        except Exception:
            return False

    if isinstance(actual, dict) and isinstance(expected, dict):
        if set(actual.keys()) != set(expected.keys()):
            return False
        return all(deep_equal(actual[k], expected[k]) for k in actual)

    return actual == expected

# Candidate Solution
__SOLUTION_CODE__

# Test Execution Driver
def run_all_tests():
    test_cases = __TEST_CASES_JSON__
    class_name = "__CLASS_NAME__"
    method_name = "__METHOD_NAME__"

    results = {
        "passed": True,
        "total": len(test_cases),
        "passed_count": 0,
        "failed_count": 0,
        "failures": []
    }

    target_class = globals().get(class_name)
    if not target_class:
        results["passed"] = False
        results["failures"].append({
            "case_index": 0,
            "error": f"Class '{class_name}' not defined in solution"
        })
        return results

    for idx, tc in enumerate(test_cases):
        args = tc.get("args", [])
        expected = tc.get("expected")
        is_design = class_name != "Solution"

        try:
            if is_design:
                # Design problem: args are [commands, arguments]
                commands, arguments = args[0], args[1]
                instance = None
                actual_outputs = []
                for cmd, arg in zip(commands, arguments):
                    if cmd == class_name or instance is None:
                        instance = target_class(*arg)
                        actual_outputs.append(None)
                    else:
                        method = getattr(instance, cmd)
                        actual_outputs.append(method(*arg))
                actual = actual_outputs
            else:
                instance = target_class()
                method = getattr(instance, method_name)
                # Auto-wrap input args for linked lists and trees if applicable
                converted_args = []
                for a in args:
                    if isinstance(a, list) and "ListNode" in str(method.__annotations__):
                        converted_args.append(build_linked_list(a))
                    elif isinstance(a, list) and "TreeNode" in str(method.__annotations__):
                        converted_args.append(build_tree(a))
                    else:
                        converted_args.append(a)
                actual = method(*converted_args)

            # Compare
            if expected is not None:
                passed = deep_equal(actual, expected)
            else:
                passed = True

            if passed:
                results["passed_count"] += 1

            else:
                results["passed"] = False
                results["failed_count"] += 1
                # Format actual for display
                fmt_actual = linked_list_to_list(actual) if isinstance(actual, ListNode) else (
                    tree_to_list(actual) if isinstance(actual, TreeNode) else actual
                )
                results["failures"].append({
                    "case_index": idx + 1,
                    "input": args,
                    "expected": expected,
                    "actual": fmt_actual,
                    "error": "Output did not match expected"
                })
        except Exception as e:
            results["passed"] = False
            results["failed_count"] += 1
            results["failures"].append({
                "case_index": idx + 1,
                "input": args,
                "expected": expected,
                "error": f"{type(e).__name__}: {str(e)}"
            })

    return results

if __name__ == "__main__":
    report = run_all_tests()
    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(report, f)
"""

class TestRunner:
    """Runs untrusted generated solutions in an isolated subprocess with strict safety limits."""
    __test__ = False

    def __init__(
        self,
        timeout_seconds: Optional[int] = None,
        max_output_chars: Optional[int] = None,
    ):
        self.timeout_seconds = timeout_seconds or settings.TEST_EXECUTION_TIMEOUT_SECONDS
        self.max_output_chars = max_output_chars or settings.MAX_OUTPUT_CHARS

    def _sanitize_env(self) -> Dict[str, str]:
        """Creates a minimal sanitized environment without any app secrets or tokens."""
        allowed_keys = {
            "SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "TEMP", "TMP",
            "PYTHONPATH", "PYTHONHOME", "COMSPEC"
        }
        clean_env = {}
        for key, val in os.environ.items():
            if key.upper() in allowed_keys:
                clean_env[key] = val
        # Guarantee no app secrets leak to subprocess
        clean_env["PYTHONUNBUFFERED"] = "1"
        return clean_env

    def run_tests(
        self,
        code: str,
        class_name: str,
        method_name: Optional[str],
        test_cases: List[Dict[str, Any]],
    ) -> TestResult:
        """
        Executes code against test cases in an isolated subprocess.
        Guarantees cleanup of temporary script files.
        """

        if not test_cases:
            # If no test cases provided, compile/import test only
            test_cases = []

        temp_dir = tempfile.mkdtemp(prefix="lc_run_")
        harness_path = Path(temp_dir) / "harness.py"
        results_path = Path(temp_dir) / "results.json"

        # Format test cases safely as JSON
        test_cases_json = json.dumps(test_cases)
        harness_content = (
            HARNESS_TEMPLATE
            .replace("__SOLUTION_CODE__", code)
            .replace("__TEST_CASES_JSON__", test_cases_json)
            .replace("__CLASS_NAME__", class_name or "Solution")
            .replace("__METHOD_NAME__", method_name or "solve")
        )


        start_time = time.time()
        try:
            with open(harness_path, "w", encoding="utf-8") as f:
                f.write(harness_content)

            clean_env = self._sanitize_env()
            cmd = [sys.executable, str(harness_path)]

            # Windows isolated subprocess execution
            proc = subprocess.Popen(
                cmd,
                cwd=temp_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=clean_env,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )

            try:
                stdout, stderr = proc.communicate(timeout=self.timeout_seconds)
            except subprocess.TimeoutExpired:
                # Force kill process tree on Windows
                proc.kill()
                if os.name == "nt":
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                return TestResult(
                    passed=False,
                    total_tests=len(test_cases),
                    failed_tests=len(test_cases),
                    failures=[{"error": f"Execution timed out after {self.timeout_seconds}s"}],
                    stderr=f"TimeoutExpired: Process exceeded {self.timeout_seconds} seconds",
                    duration_ms=(time.time() - start_time) * 1000
                )

            duration_ms = (time.time() - start_time) * 1000

            # Truncate stdout/stderr to prevent memory DOS
            stdout = stdout[:self.max_output_chars] if stdout else ""
            stderr = stderr[:self.max_output_chars] if stderr else ""

            if proc.returncode != 0:
                return TestResult(
                    passed=False,
                    total_tests=len(test_cases),
                    failed_tests=len(test_cases),
                    failures=[{
                        "error": f"Subprocess exited with code {proc.returncode}",
                        "stderr": stderr
                    }],
                    stdout=stdout,
                    stderr=stderr,
                    duration_ms=duration_ms
                )

            # Read result JSON
            if results_path.exists():
                with open(results_path, "r", encoding="utf-8") as rf:
                    res_json = json.load(rf)
                return TestResult(
                    passed=res_json.get("passed", False),
                    total_tests=res_json.get("total", len(test_cases)),
                    passed_tests=res_json.get("passed_count", 0),
                    failed_tests=res_json.get("failed_count", 0),
                    failures=res_json.get("failures", []),
                    stdout=stdout,
                    stderr=stderr,
                    duration_ms=round(duration_ms, 2)
                )

            return TestResult(
                passed=False,
                total_tests=len(test_cases),
                failed_tests=len(test_cases),
                failures=[{"error": "No results generated by test harness", "stderr": stderr}],
                stdout=stdout,
                stderr=stderr,
                duration_ms=duration_ms
            )

        except Exception as e:
            return TestResult(
                passed=False,
                total_tests=len(test_cases),
                failed_tests=len(test_cases),
                failures=[{"error": f"Runner harness exception: {e}"}],
                duration_ms=(time.time() - start_time) * 1000
            )
        finally:
            # Guarantees cleanup of temporary test files and sandbox directory
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass
