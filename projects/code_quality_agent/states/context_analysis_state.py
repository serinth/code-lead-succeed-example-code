from typing import List, Optional
from langchain_core.messages import BaseMessage
from pydantic import BaseModel
from models.employee import Employee
from states.context_analysis_feedback import ContextAnalysisFeedback

class ContextAnalysisState(BaseModel):
    employee: Employee
    days_to_look_back: int
    messages: Optional[List[BaseMessage]] = None
    analysis_feedback: Optional[ContextAnalysisFeedback] = None