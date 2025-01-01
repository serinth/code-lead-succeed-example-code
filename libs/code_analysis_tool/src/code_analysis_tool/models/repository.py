from dataclasses import dataclass
from typing import Optional
from .user import User
@dataclass
class Repository:
    """Platform-agnostic repository model."""
    id: str
    name: str
    full_name: str
    owner: User
    description: Optional[str] = None
    private: bool = False