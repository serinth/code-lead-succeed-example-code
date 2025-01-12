from typing import List
import pytest
from loguru import logger
from dataclasses import dataclass
from models.employee import Employee
from models.levels import SeniorityLevel
from states.context_analysis_state import ContextAnalysisState
from graphs.context_analysis_graph import create_graph
from langchain_ollama.llms import OllamaLLM

@dataclass
class TestCase:
    name: str
    employee: Employee
    days_to_look_back: int
    expected_has_context: bool
    confidence_tolerance: float = 0.2  # Default tolerance of 0.2 for confidence checks


test_cases: List[TestCase] = [
        TestCase(
            name="New junior with no PRs",
            employee=Employee(
                id="test1@company.com",
                cvs_username="test1",
                seniority_level=SeniorityLevel.JUNIOR.value,
                expected_prs_per_week=2,
                tenure_months=1,
                pr_count=0
            ),
            days_to_look_back=30,
            expected_has_context=False,
        ),
        TestCase(
            name="Senior with sufficient PRs (more than enough)",
            employee=Employee(
                id="test2@company.com",
                cvs_username="test2",
                seniority_level=SeniorityLevel.SENIOR.value,
                expected_prs_per_week=3,
                tenure_months=12,
                pr_count=15
            ),
            days_to_look_back=30,
            expected_has_context=True,
        ),
        TestCase(
            name="Mid level with borderline PR count",
            employee=Employee(
                id="test3@company.com",
                cvs_username="test3",
                seniority_level=SeniorityLevel.MID_LEVEL.value,
                expected_prs_per_week=2,
                tenure_months=6,
                pr_count=5
            ),
            days_to_look_back=30,
            expected_has_context=True,
        ),
        TestCase(
            name="Principal with a low PR count (minimum required)",
            employee=Employee(
                id="test4@company.com",
                cvs_username="test4",
                seniority_level=SeniorityLevel.PRINCIPAL.value,
                expected_prs_per_week=1,
                tenure_months=24,
                pr_count=4
            ),
            days_to_look_back=30,
            expected_has_context=True,
        ),
        TestCase(
            name="Staff engineer with low PR count but long tenure",
            employee=Employee(
                id="test5@company.com",
                cvs_username="test5",
                seniority_level=SeniorityLevel.STAFF.value,
                expected_prs_per_week=1,
                tenure_months=36,
                pr_count=3
            ),
            days_to_look_back=30,
            expected_has_context=True,
        ),
        TestCase(
            name="Intern with high PR velocity",
            employee=Employee(
                id="test6@company.com",
                cvs_username="test6",
                seniority_level=SeniorityLevel.INTERN.value,
                expected_prs_per_week=3,
                tenure_months=2,
                pr_count=15
            ),
            days_to_look_back=30,
            expected_has_context=True,
        ),
        TestCase(
            name="Mid level with exactly minimum required PRs",
            employee=Employee(
                id="test7@company.com",
                cvs_username="test7",
                seniority_level=SeniorityLevel.MID_LEVEL.value,
                expected_prs_per_week=2,
                tenure_months=3,
                pr_count=6
            ),
            days_to_look_back=30,
            expected_has_context=True,
        ),
        TestCase(
            name="Senior with borderline PR count",
            employee=Employee(
                id="test8@company.com",
                cvs_username="test8",
                seniority_level=SeniorityLevel.SENIOR.value,
                expected_prs_per_week=2,
                tenure_months=12,
                pr_count=5
            ),
            days_to_look_back=30,
            expected_has_context=True,
        ),
        TestCase(
            name="Senior with extremely low PR count",
            employee=Employee(
                id="test9@company.com",
                cvs_username="test9",
                seniority_level=SeniorityLevel.SENIOR.value,
                expected_prs_per_week=1,
                tenure_months=48,
                pr_count=1
            ),
            days_to_look_back=30,
            expected_has_context=False,
        ),
        TestCase(
            name="New starter Senior with low PR count",
            employee=Employee(
                id="test10@company.com",
                cvs_username="test10",
                seniority_level=SeniorityLevel.SENIOR.value,
                expected_prs_per_week=1,
                tenure_months=1,
                pr_count=1
            ),
            days_to_look_back=7,
            expected_has_context=False,
        )
    ]


@pytest.fixture
def llm():
    return OllamaLLM(
        model="codeqwen:latest",
        temperature=0.2,
        base_url="http://localhost:11434"
    )


@pytest.mark.parametrize("test_case", test_cases)
def test_context_analysis(
    test_case: TestCase,
    llm: OllamaLLM
) -> None:
    try:
        # Arrange
        initial_state = ContextAnalysisState(
            employee=test_case.employee,
            days_to_look_back=test_case.days_to_look_back,
            messages=[],
            analysis_feedback=None
        )

        # Act
        graph = create_graph(llm=llm)
        final_state = graph.invoke(initial_state)
        final_state = ContextAnalysisState(**final_state)

        # Assert
        assert final_state.analysis_feedback is not None, "Analysis feedback should not be None"
        
        assert final_state.analysis_feedback.has_sufficient_context == test_case.expected_has_context, \
            f"Expected has_sufficient_context to be {test_case.expected_has_context} for case '{test_case.name}'"
        
        assert 0 <= final_state.analysis_feedback.confidence <= 1, \
            f"Confidence should be between 0 and 1 for case '{test_case.name}'"
        
        # Check if confidence is within tolerance 
        upper_bound = final_state.analysis_feedback.confidence + test_case.confidence_tolerance
        lower_bound = final_state.analysis_feedback.confidence - test_case.confidence_tolerance
        assert final_state.analysis_feedback.confidence <= upper_bound and final_state.analysis_feedback.confidence >= lower_bound, \
            f"Confidence was not within tolerance for case '{test_case.name}', got {final_state.analysis_feedback.confidence} with a tolerance of {test_case.confidence_tolerance}"
    
        assert len(final_state.analysis_feedback.reasoning) > 30, \
            f"Reasoning should be detailed for case '{test_case.name}'"

        # Log the results for analysis
        logger.info(f"""
        Test Case: {test_case.name}
        Expected Context: {test_case.expected_has_context}
        Actual Context: {final_state.analysis_feedback.has_sufficient_context}
        Confidence: {final_state.analysis_feedback.confidence}
        Reasoning: {final_state.analysis_feedback.reasoning}
        """)

    except Exception as e:
        logger.error(f"Test failed for case '{test_case.name}': {str(e)}")
        raise

def test_error_handling(
    llm: OllamaLLM,
) -> None:
    try:
        # Test with invalid state
        invalid_state = None
        graph = create_graph(llm=llm)
        
        with pytest.raises(Exception):
            graph.invoke(invalid_state)

    except Exception as e:
        logger.error(f"Error handling test failed: {str(e)}")
        raise