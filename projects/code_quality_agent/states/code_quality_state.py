from datetime import datetime
from enum import Enum
from typing import List, Optional, Callable

from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field

from models.employee import Employee


class PRQualityAssessment(BaseModel):
    pr_id: str = Field(description="ID of the PR")
    title: str = Field(description="Title of the PR")
    number: int = Field(description="PR number")
    description: str = Field(description="Description of the PR")
    ai_description: str = Field(description="Description of the PR by the AI", default="")
    quality_score: int = Field(description="Float value between 0 and 100 on how good the code is where 100 is the highest quality", default=0)
    testing_suggestions: List[str] = Field(description="List of suggestions for improving testing and edge cases", default=[])
    security_concerns: List[str] = Field(description="List of security concerns linked to the PR", default=[])
    maintainability_suggestions: List[str] = Field(description="List of suggestions for improving maintainability and readability", default=[])
    performance_suggestions: List[str] = Field(description="List of suggestions for improving performance with BigO notation", default=[])
    confidence: float  = Field(description="Float value between 0 and 1 on how confident the AI is on its assessment", default=0.0)

class CodeQualityState(BaseModel):
    employee: Employee = Field(description="Employee object")
    messages: List[BaseMessage] = Field(description="List of messages")
    assessment: Optional[PRQualityAssessment] = Field(description="Code quality assessment", default=None)


class QualityLevel(int, Enum):
    WORST = 0
    BEST = 100


class Decision(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


class Recommendation(BaseModel):
    line_numbers: List[int] = Field(
        description="Lines of code where the issue is identified. Optional if the actual code snippet is provided.",
        default_factory=list
    )
    code_snippet: Optional[str] = Field(
        description="Actual code snippet where the issue is identified, if line numbers are not provided.",
        default=None
    )
    issue: str = Field(
        description="Description of the identified issue."
    )
    recommended_fix: str = Field(
        description="Suggested fix or improvement for the identified issue."
    )


class BaseEvaluation(BaseModel):
    score: QualityLevel = Field(
        description="Score, where 0 represents WORST and 100 represents BEST.",
        default=QualityLevel.WORST
    )
    threshold: int = Field(
        description="Threshold score for passing (0-100).",
        ge=QualityLevel.WORST,
        le=QualityLevel.BEST,
        default=QualityLevel.BEST
    )
    recommendations: List[Recommendation] = Field(
        description="List of recommendations for improving this aspect.",
        default_factory=list
    )

    @property
    def final_decision(self) -> Decision:
        """Calculate the final decision based on the score and threshold."""
        return Decision.PASS if self.score >= self.threshold else Decision.FAIL


class ReadabilityAndMaintainability(BaseEvaluation):
    semantic_understanding: Optional[str] = Field(
        description="Assessment of semantic understanding, including intent, complexity, and logical coherence.",
        default=None
    )
    design_pattern_recognition: Optional[str] = Field(
        description="Evaluation of the use of design patterns, anti-patterns, and adherence to SOLID principles.",
        default=None
    )
    documentation_quality: Optional[str] = Field(
        description="Assessment of documentation quality, including value-added comments, missing documentation, and consistency with code.",
        default=None
    )


class Security(BaseEvaluation):
    input_validation: Optional[str] = Field(
        description="Assessment of input validation mechanisms to prevent malicious input.",
        default=None
    )
    authentication_and_authorization: Optional[str] = Field(
        description="Evaluation of authentication and authorization practices.",
        default=None
    )
    cryptographic_weakness: Optional[str] = Field(
        description="Assessment of cryptographic weaknesses in data protection, both at rest and in transit.",
        default=None
    )
    error_handling_and_logging: Optional[str] = Field(
        description="Evaluation of error handling and logging mechanisms for sensitive information exposure.",
        default=None
    )
    dependency_management: Optional[str] = Field(
        description="Analysis of third-party dependencies for known vulnerabilities.",
        default=None
    )
    input_validation_issues: Optional[str] = Field(
        description="Detailed description of input validation issues.",
        default=None
    )
    data_exposure_risks: Optional[str] = Field(
        description="Assessment of potential data exposure risks.",
        default=None
    )
    injection_vulnerabilities: Optional[str] = Field(
        description="Analysis of injection vulnerabilities, such as SQL or command injection.",
        default=None
    )
    hardcoded_secrets: Optional[str] = Field(
        description="Evaluation of hardcoded secrets such as API keys or passwords.",
        default=None
    )
    race_conditions: Optional[str] = Field(
        description="Assessment of potential race conditions in the code.",
        default=None
    )
    memory_safety_issues: Optional[str] = Field(
        description="Evaluation of memory safety issues, such as buffer overflows.",
        default=None
    )
    business_logic_flaws: Optional[str] = Field(
        description="Analysis of business logic flaws that could be exploited.",
        default=None
    )


class Testability(BaseEvaluation):
    modularity: Optional[str] = Field(
        description="Evaluation of the modularity of the code, including clear separation of concerns and encapsulation.",
        default=None
    )
    test_coverage: Optional[str] = Field(
        description="Assessment of the test coverage, focusing on critical paths and edge cases.",
        default=None
    )
    ease_of_testing: Optional[str] = Field(
        description="Evaluation of how easily the code can be tested, including the presence of test hooks or dependencies.",
        default=None
    )
    evaluator_notes: Optional[str] = Field(
        description="Additional notes or remarks by the evaluator for context or clarification.",
        default=None
    )


class PullRequestEvaluation(BaseModel):
    pr_id: str = Field(
        description="Identifier for the pull request."
    )
    readability_and_maintainability: ReadabilityAndMaintainability = Field(
        description="Evaluation of code readability and maintainability aspects for this PR."
    )
    security: Security = Field(
        description="Evaluation of code security aspects for this PR."
    )
    testability: Testability = Field(
        description="Evaluation of code testability aspects for this PR."
    )
    decision_function: Callable[[List[BaseEvaluation]], Decision] = Field(
        description="Custom decision function to calculate the final decision based on all BaseEvaluation instances.",
        default=lambda evaluations: Decision.PASS if all(
            e.final_decision == Decision.PASS for e in evaluations) else Decision.FAIL
    )

    @property
    def final_decision(self) -> Decision:
        """Calculate the final decision based on the BaseEvaluation instances' final decisions."""
        evaluations = [
            self.readability_and_maintainability,
            self.security,
            self.testability
        ]
        return self.decision_function(evaluations)


class CodeQualityEvaluation(BaseModel):
    employee: str = Field(
        description="Employee object"
    )
    messages: List[str] = Field(
        description="List of messages",
        default_factory=list
    )
    pull_requests: List[PullRequestEvaluation] = Field(
        description="Evaluations for individual pull requests.",
        default_factory=list
    )
    timestamp: datetime = Field(
        description="The time when this evaluation was performed.",
        default_factory = datetime.now
    )

    @property
    def final_decision(self) -> Decision:
        """Calculate the final decision based on the evaluations of all PRs and their category decisions."""
        if all(pr.final_decision == Decision.PASS for pr in self.pull_requests):
            return Decision.PASS
        return Decision.FAIL
