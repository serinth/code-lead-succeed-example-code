from typing import List
from pydantic import Field, BaseModel


class ContextAnalysisFeedback(BaseModel):
    has_sufficient_context: bool = Field(description="Boolean of whether or not LM needs to fetch more context. True when there's enough data from PRs and ticket references. False when there isn't enough to analyze the employee's code quality")
    reasoning: str = Field(description="String on the reasoning why the AI thinks more context is required")
    confidence: float = Field(description="Float value between 0 and 1 on how confident the AI is that it needs more context")