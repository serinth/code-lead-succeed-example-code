from pydantic import BaseModel, Field
from typing import List, Optional
from models.quality_level import QualityLevel
from models.decision import Decision
from states.recommendation import Recommendation

class BaseEvaluation(BaseModel):
    pr_id: str = Field(
        description="ID of the PR"
    )
    score: int = Field(
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
        default=[]
    )

    @property
    def final_decision(self) -> Decision:
        """Calculate the final decision based on the score and threshold."""
        return Decision.PASS if self.score >= self.threshold else Decision.FAIL