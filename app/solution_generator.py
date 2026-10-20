from typing import Any, Dict, List, Optional
from app.config import logger
from app.llm_client import OllamaClient
from app.models import GenerationResult

INITIAL_PROMPT_TEMPLATE = """You are an expert Python algorithmic developer solving a LeetCode problem.

PROBLEM: {title} ({difficulty})
CATEGORY: {category}

DESCRIPTION:
{statement}

STARTER CODE TEMPLATE:
```python
{starter_code}
```

REQUIREMENTS:
1. Provide the complete, working Python 3 implementation.
2. Must match the exact class name `{class_name}` and method `{method_name}`.
3. Import all necessary types from `typing` if needed (e.g., List, Optional, Dict, Tuple).
4. Do NOT include test drivers, explanations, or sample runs.
5. Return ONLY the Python code enclosed in a ```python ... ``` markdown block.
"""

class SolutionGenerator:
    """Generates initial LeetCode solutions using Ollama LLM."""

    def __init__(self, client: Optional[OllamaClient] = None):
        self.client = client or OllamaClient()

    def generate_solution(
        self,
        title: str,
        category: str,
        difficulty: str,
        statement: str,
        starter_code: Optional[str] = None,
        class_name: str = "Solution",
        method_name: Optional[str] = None,
    ) -> GenerationResult:
        """Generates a Python 3 candidate solution for the given problem."""
        default_starter = starter_code or f"class {class_name}:\n    def {method_name or 'solve'}(self):\n        pass"
        prompt = INITIAL_PROMPT_TEMPLATE.format(
            title=title,
            category=category,
            difficulty=difficulty,
            statement=statement or "Solve the problem efficiently.",
            starter_code=default_starter,
            class_name=class_name,
            method_name=method_name or "solve",
        )

        logger.info(f"Generating solution for '{title}' with model '{self.client.model}'...")
        res = self.client.generate(
            prompt=prompt,
            expected_class=class_name,
            expected_method=method_name,
        )
        return res
