from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict

from .user import User
from .repository import Repository

@dataclass
class PullRequest:
    """Platform-agnostic pull request model."""
    id: str
    number: int
    title: str
    author: User
    repository: Repository
    created_at: datetime
    merged_at: Optional[datetime] = None
    merged: bool = False
    description: Optional[str] = None
    file_diffs: Dict[str, str] = field(default_factory=dict)  # filename -> diff content 