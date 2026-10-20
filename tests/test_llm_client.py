from unittest.mock import MagicMock, patch
from app.llm_client import OllamaClient

def test_code_extraction():
    """Test extracting clean code from varied LLM response formats."""
    client = OllamaClient()

    # Markdown python block
    resp1 = "Here is the code:\n```python\nclass Solution:\n    def solve(self):\n        return True\n```\nHope it helps!"
    assert client.extract_code(resp1) == "class Solution:\n    def solve(self):\n        return True"

    # Generic code block
    resp2 = "```\nclass Solution:\n    pass\n```"
    assert client.extract_code(resp2) == "class Solution:\n    pass"

    # Raw text without code fences
    resp3 = "class Solution:\n    def solve(self):\n        pass"
    assert client.extract_code(resp3) == "class Solution:\n    def solve(self):\n        pass"

def test_invalid_python_handling():
    """Test handling of invalid Python syntax."""
    client = OllamaClient()
    invalid_code = "def bad_syntax(self return 123"
    is_valid, has_cls, has_meth, err = client.validate_ast(invalid_code, "Solution", "solve")
    assert is_valid is False
    assert "SyntaxError" in err

def test_ast_class_and_method_verification():
    """Test verification of required class and method."""
    client = OllamaClient()
    code = """
class Solution:
    def twoSum(self, nums, target):
        return [0, 1]
"""
    # Matching class and method
    is_valid, has_cls, has_meth, err = client.validate_ast(code, expected_class="Solution", expected_method="twoSum")
    assert is_valid is True
    assert has_cls is True
    assert has_meth is True
    assert err is None

    # Missing class
    _, has_cls_wrong, _, _ = client.validate_ast(code, expected_class="MinStack", expected_method="twoSum")
    assert has_cls_wrong is False

    # Missing method
    _, _, has_meth_wrong, _ = client.validate_ast(code, expected_class="Solution", expected_method="solve")
    assert has_meth_wrong is False

@patch("requests.post")
def test_mock_llm_generation(mock_post):
    """Test LLM generation call with mocked Ollama API response."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "response": "```python\nclass Solution:\n    def test(self):\n        return 42\n```"
    }

    client = OllamaClient()
    result = client.generate(
        prompt="Write a test function",
        expected_class="Solution",
        expected_method="test",
    )
    assert result.is_valid_python is True
    assert result.has_target_class is True
    assert result.has_target_method is True
    assert "return 42" in result.code
