from pydantic import BaseModel, Field
from typing import List, Optional

class Recommendation(BaseModel):
    file_name: str = Field(
        description="Name of the file where the issue is identified."
    )
    line_numbers: List[int] = Field(
        description="Lines of code where the issue is identified. Optional if the actual code snippet is provided.",
        default=[]
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