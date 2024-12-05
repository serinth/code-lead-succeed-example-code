from datetime import datetime
from typing import Optional
from dataclasses import dataclass


@dataclass
class Build:
    """
    Represents a build entity with its associated metadata
    Should match the Schema defined in setup.py
    It's all string types to make it easy to insert into BigQuery
    """
    id: str
    created_at: str
    commit: str
    branch: str
    repo: str
    duration_secs: int
    closed_at: Optional[str] = None
