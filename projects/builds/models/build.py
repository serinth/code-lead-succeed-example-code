from datetime import datetime
from typing import Optional
from dataclasses import dataclass


@dataclass
class Build():
    """Represents a build entity with its associated metadata"""
    created_at: datetime
    commit: str
    branch: str
    repo: str
    closed_at: Optional[datetime] = None

