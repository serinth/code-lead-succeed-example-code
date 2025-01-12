from typing import List
import pytest
from unittest.mock import Mock
from loguru import logger
from dataclasses import dataclass
from langchain_ollama.llms import OllamaLLM
from datetime import datetime
from models.employee import Employee
from models.levels import SeniorityLevel
from states.code_quality_state import CodeQualityState
from graphs.code_quality_graph import create_graph
from code_analysis_tool.models.pull_request import PullRequest
from code_analysis_tool.models.user import User
from code_analysis_tool.models.repository import Repository

@dataclass
class TestCase:
    name: str
    employee: Employee
    pr: PullRequest
    expected_min_quality_score: float
    expected_min_confidence: float
    confidence_tolerance: float = 0.2

# Example diff for a well-structured code change
GOOD_CODE_DIFF = """diff --git a/src/utils/validation.py b/src/utils/validation.py
--- a/src/utils/validation.py
+++ b/src/utils/validation.py
@@ -1,10 +1,15 @@
 from typing import Dict, Any, Optional
+from pydantic import BaseModel, ValidationError
-def validate_input(data: Dict[str, Any]) -> bool:
-    if not isinstance(data, dict):
-        return False
-    return True
+class InputData(BaseModel):
+    name: str
+    age: Optional[int] = None
+    email: str
 
+def validate_input(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
+    try:
+        InputData(**data)
+        return True, None
+    except ValidationError as e:
+        return False, str(e)"""

user = User(
        id="user_id",
        login="user_login"
    )

repo = Repository(
        id="repository_id",
        name="repository_name",
        full_name="repository_full_name",
        owner=user
    )

test_cases: List[TestCase] = [
    TestCase(
        name="Senior engineer submitting well-structured code",
        employee=Employee(
            id="senior@company.com",
            cvs_username="senior_dev",
            seniority_level=SeniorityLevel.SENIOR.value,
            expected_prs_per_week=2,
            tenure_months=24,
            pr_count=3
        ),
        pr=PullRequest(
            id="id",
            number=1,
            title="Improve input validation with Pydantic",
            author=user,
            repository=repo,
            created_at=datetime.now(),
            merged=False,
            merged_at=None,
            description="Improve input validation with Pydantic",
            file_diffs= {
                "src/utils/validation.py": GOOD_CODE_DIFF
            }
        ),
        expected_min_quality_score=80.0,
        expected_min_confidence=0.8
    )
]

@pytest.fixture
def llm() -> OllamaLLM:
    return OllamaLLM(
        model="codeqwen:latest",
        temperature=0.2,
        base_url="http://localhost:11434"
    )

@pytest.mark.parametrize("test_case", test_cases)
def test_code_quality_analysis(
    test_case: TestCase,
    llm: OllamaLLM
) -> None:
    try:
        # Arrange
        initial_state = CodeQualityState(
            employee=test_case.employee,
            messages=[],
            assessment=None
        )

        # Act
        graph = create_graph(llm=llm, pr=test_case.pr)
        final_state = graph.invoke(initial_state)
        final_state = CodeQualityState(**final_state)

        # Assert
        assert final_state.assessment is not None, "Assessment should not be None"
        
        assert final_state.assessment.quality_score >= test_case.expected_min_quality_score, \
            f"Quality score below minimum for case '{test_case.name}'"
        
        assert final_state.assessment.confidence >= test_case.expected_min_confidence, \
            f"Confidence below minimum for case '{test_case.name}'"
        
        assert (len(final_state.assessment.maintainability_suggestions) > 0 or
                len(final_state.assessment.performance_suggestions) > 0 or
                len(final_state.assessment.security_concerns) > 0 or
                len(final_state.assessment.testing_suggestions) > 0), \
            f"No suggestions found for case '{test_case.name}'"
        
    except Exception as e:
        logger.error(f"Test failed for case '{test_case.name}': {str(e)}")
        raise

def test_error_handling(
    llm: OllamaLLM
) -> None:
    try:
        # Test with invalid state
        invalid_state = None
        pr = Mock(spec=PullRequest)
        graph = create_graph(llm=llm, pr=pr)
        
        with pytest.raises(Exception):
            graph.invoke(invalid_state)

    except Exception as e:
        logger.error(f"Error handling test failed: {str(e)}")
        raise 