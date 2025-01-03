from pydantic import BaseModel
from models.levels import SeniorityLevel

class Employee(BaseModel):
    id: str
    cvs_username: str
    seniority_level: SeniorityLevel
    expected_prs_per_week: int = 3
    tenure_months: int
    pr_count: int = 0