from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
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


class ReadabilityAndMaintainability(BaseModel):
    semantic_understanding: str = Field(
        description="Assessment of semantic understanding, including intent, complexity, and logical coherence."
    )
    design_pattern_recognition: str = Field(
        description="Evaluation of the use of design patterns, anti-patterns, and adherence to SOLID principles."
    )
    documentation_quality: str = Field(
        description="Assessment of documentation quality, including value-added comments, missing documentation, and consistency with code."
    )
    score: int = Field(
        description="Score for readability and maintainability (0-100).",
        ge=0,
        le=100
    )
    threshold: int = Field(
        description="Threshold score for passing (0-100).",
        ge=0,
        le=100
    )

    @property
    def final_decision(self) -> str:
        """Calculate the final decision based on the score and threshold."""
        return "PASS" if self.score >= self.threshold else "FAIL"


class Security(BaseModel):
    input_validation: str = Field(
        description="Assessment of input validation mechanisms to prevent malicious input."
    )
    authentication_and_authorization: str = Field(
        description="Evaluation of authentication and authorization practices."
    )
    encryption_practices: str = Field(
        description="Assessment of data encryption practices, both at rest and in transit."
    )
    error_handling_and_logging: str = Field(
        description="Evaluation of error handling and logging mechanisms for sensitive information exposure."
    )
    dependency_management: str = Field(
        description="Analysis of third-party dependencies for known vulnerabilities."
    )
    score: int = Field(
        description="Score for security (0-100).",
        ge=0,
        le=100
    )
    threshold: int = Field(
        description="Threshold score for passing (0-100).",
        ge=0,
        le=100
    )

    @property
    def final_decision(self) -> str:
        """Calculate the final decision based on the score and threshold."""
        return "PASS" if self.score >= self.threshold else "FAIL"


class Testability(BaseModel):
    modularity: str = Field(
        description="Evaluation of the modularity of the code, including clear separation of concerns and encapsulation."
    )
    test_coverage: str = Field(
        description="Assessment of the test coverage, focusing on critical paths and edge cases."
    )
    ease_of_testing: str = Field(
        description="Evaluation of how easily the code can be tested, including the presence of test hooks or dependencies."
    )
    evaluator_notes: Optional[str] = Field(
        description="Additional notes or remarks by the evaluator for context or clarification.",
        default=None
    )
    score: int = Field(
        description="Score for testability (0-100).",
        ge=0,
        le=100
    )
    threshold: int = Field(
        description="Threshold score for passing (0-100).",
        ge=0,
        le=100
    )

    @property
    def final_decision(self) -> str:
        """Calculate the final decision based on the score and threshold."""
        return "PASS" if self.score >= self.threshold else "FAIL"


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

    @property
    def final_decision(self) -> str:
        """Calculate the final decision based on the categories' final decisions."""
        if all(
                category.final_decision == "PASS" for category in [
                    self.readability_and_maintainability,
                    self.security,
                    self.testability
                ]
        ):
            return "PASS"
        return "FAIL"


class CodeQualityEvaluation(BaseModel):
    employee: Employee = Field(
        description="Employee object"
    )
    messages: List[BaseMessage] = Field(
        description="List of messages"
    )
    assessment: Optional[PRQualityAssessment] = Field(
        description="Code quality assessment",
        default=None
    )
    pull_requests: List[PullRequestEvaluation] = Field(
        description="Evaluations for individual pull requests."
    )

    @property
    def final_decision(self) -> str:
        """Calculate the final decision based on the evaluations of all PRs and their category decisions."""
        if all(pr.final_decision == "PASS" for pr in self.pull_requests):
            return "PASS"
        return "FAIL"
