from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    """Platform-agnostic user model."""
    id: str
    login: str
    name: Optional[str] = None
    email: Optional[str] = None