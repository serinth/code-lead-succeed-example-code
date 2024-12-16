from typing import List
from pydantic import Field, BaseModel

class CodeReviewFeedback(BaseModel):
    readability: List[str] = Field(description="List of readability improvements")
    testability: List[str] = Field(description="List of testability improvements")
    security: List[str] = Field(description="List of security concerns and improvements")