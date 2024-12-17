import pytest
from code_reviewer import CodeReviewer
from unittest.mock import Mock, patch

@pytest.fixture
def code_reviewer() -> CodeReviewer:
    return CodeReviewer(model_name="test_model")

def test_initialize_components(code_reviewer: CodeReviewer) -> None:
    assert code_reviewer.llm is not None
    assert code_reviewer.output_parser is not None
    assert code_reviewer.prompt is not None
    assert code_reviewer.chain is not None

def test_extract_json(code_reviewer: CodeReviewer) -> None:
    test_input = 'Some text before {"key": "value"} some text after'
    expected = '{"key": "value"}'
    
    result = code_reviewer._extract_json(test_input)
    assert result == expected

@pytest.mark.asyncio
async def test_review_code_success(code_reviewer: CodeReviewer) -> None:
    test_diff = """
    @@ -1,5 +1,7 @@
    -def test():
    +def test() -> None:
         pass
    """
    
    stub_response = Mock()
    stub_response.readability = ["Use better function name"]
    stub_response.testability = ["Add unit tests"]
    stub_response.security = []
    
    code_reviewer.chain=Mock()
    code_reviewer.chain.invoke.return_value = stub_response
    
    result = code_reviewer.review_code(test_diff)
    
    assert "readability" in result
    assert "testability" in result
    assert "security" in result
    assert result["readability"] == ["Use better function name"]
    assert result["testability"] == ["Add unit tests"]
    assert result["security"] == []

def test_review_code_error_handling(code_reviewer: CodeReviewer) -> None:
    test_diff = "invalid diff"

    code_reviewer.chain = Mock()
    code_reviewer.chain.invoke.side_effect = Exception("Test error")
    
    result = code_reviewer.review_code(test_diff)

    assert "error" in result
    assert "Failed to analyze code: Test error" in result["error"][0]
    assert result["readability"] == []
    assert result["testability"] == []
    assert result["security"] == [] 