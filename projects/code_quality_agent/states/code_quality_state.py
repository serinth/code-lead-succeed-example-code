from datetime import datetime
from typing import List, Optional, Callable
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field
from models.employee import Employee
from states.base_evaluation import BaseEvaluation
from models.decision import Decision


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


class CodeQualityEvaluation(BaseModel):
    employee_id: str = Field(
        description="Employee id"
    )
    messages: List[BaseMessage] = Field(
        description="List of messages",
        default=[]
    )
    evaluation: BaseEvaluation = Field(
        description="Evaluations for individual pull requests.",
        default=None
    )
    timestamp: datetime = Field(
        description="The time when this evaluation was performed.",
        default_factory = datetime.now
    )
