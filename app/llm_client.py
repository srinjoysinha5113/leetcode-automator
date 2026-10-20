import ast
import re
import time
from typing import Optional, Tuple
import requests
from app.config import logger, settings
from app.models import GenerationResult

class OllamaClient:
    """Client for local Ollama LLM integration."""

    def __init__(
        self,
        host: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        timeout: Optional[int] = None,
    ):
        self.host = (host or settings.OLLAMA_HOST).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.temperature = temperature if temperature is not None else settings.OLLAMA_TEMPERATURE
        self.timeout = timeout or settings.OLLAMA_TIMEOUT_SECONDS

    def check_health(self) -> Tuple[bool, str]:
        """Verifies that the Ollama service is reachable and the model is downloaded."""
        try:
            resp = requests.get(f"{self.host}/api/tags", timeout=5)
            if resp.status_code != 200:
                return False, f"Ollama returned HTTP status {resp.status_code}"
            
            data = resp.json()
            models = [m.get("name") for m in data.get("models", [])]
            # Match either exact name or prefix (e.g. llama3.2:3b matching llama3.2:3b:latest)
            matched = any(
                self.model == m or self.model in m or m.startswith(self.model)
                for m in models
            )
            if not matched:
                return (
                    False,
                    f"Model '{self.model}' not found in Ollama. Available models: {models}. Run: ollama pull {self.model}"
                )
            return True, f"Ollama is healthy. Model '{self.model}' is available."
        except requests.ConnectionError:
            return (
                False,
                f"Cannot connect to Ollama at {self.host}. Please start Ollama with 'ollama serve'."
            )
        except Exception as e:
            return False, f"Ollama health check error: {e}"

    def extract_code(self, response_text: str) -> str:
        """Extracts executable Python code from markdown blocks or raw text."""
        # Check for ```python ... ```
        py_blocks = re.findall(r"```python\s*(.*?)\s*```", response_text, re.DOTALL | re.IGNORECASE)
        if py_blocks:
            # Return the largest block (most likely the complete solution)
            return max(py_blocks, key=len).strip()

        # Check for generic code blocks ``` ... ```
        generic_blocks = re.findall(r"```\s*(.*?)\s*```", response_text, re.DOTALL)
        if generic_blocks:
            return max(generic_blocks, key=len).strip()

        # Fallback: find text starting from class definition or imports
        lines = response_text.splitlines()
        code_lines = []
        started = False
        for line in lines:
            if not started and (
                line.startswith("class ") or
                line.startswith("import ") or
                line.startswith("from ") or
                line.startswith("def ")
            ):
                started = True
            if started:
                code_lines.append(line)

        if code_lines:
            return "\n".join(code_lines).strip()

        return response_text.strip()

    def validate_ast(
        self,
        code: str,
        expected_class: str = "Solution",
        expected_method: Optional[str] = None
    ) -> Tuple[bool, bool, bool, Optional[str]]:
        """
        Validates code syntax using AST and verifies expected class and method exist.
        Returns: (is_valid_python, has_class, has_method, error_message)
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, False, False, f"SyntaxError at line {e.lineno}, col {e.offset}: {e.msg}"
        except Exception as e:
            return False, False, False, f"Parse error: {e}"

        has_class = False
        has_method = False

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if node.name == expected_class:
                    has_class = True
                    if expected_method:
                        for subnode in node.body:
                            if isinstance(subnode, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                if subnode.name == expected_method:
                                    has_method = True
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if expected_method and node.name == expected_method:
                    has_method = True

        # If no specific method was expected, treat has_method as True
        if not expected_method:
            has_method = True

        return True, has_class, has_method, None

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        expected_class: str = "Solution",
        expected_method: Optional[str] = None,
        max_retries: int = 2
    ) -> GenerationResult:
        """Calls the local Ollama API to generate a Python solution."""
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt or "You are an expert algorithms engineer. Write clean, optimal, bug-free Python 3 code for LeetCode.",
            "stream": False,
            "options": {
                "temperature": self.temperature,
            }
        }

        last_error = None
        for attempt in range(max_retries + 1):
            start_time = time.time()
            try:
                resp = requests.post(url, json=payload, timeout=self.timeout)
                duration = time.time() - start_time
                resp.raise_for_status()

                data = resp.json()
                raw_response = data.get("response", "")
                code = self.extract_code(raw_response)

                is_valid, has_cls, has_meth, err = self.validate_ast(
                    code,
                    expected_class=expected_class,
                    expected_method=expected_method
                )

                return GenerationResult(
                    code=code,
                    is_valid_python=is_valid,
                    has_target_class=has_cls,
                    has_target_method=has_meth,
                    error=err,
                    duration_seconds=round(duration, 3),
                    model=self.model,
                )
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Ollama generation attempt {attempt + 1} failed: {e}")
                time.sleep(1)

        return GenerationResult(
            code="",
            is_valid_python=False,
            has_target_class=False,
            has_target_method=False,
            error=f"All {max_retries + 1} generation attempts failed: {last_error}",
            duration_seconds=0.0,
            model=self.model,
        )
