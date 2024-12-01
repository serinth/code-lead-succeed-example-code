from dataclasses import dataclass
from state_manager.interfaces import BaseState
from datetime import datetime
from typing import Optional

@dataclass
class LastRunState(BaseState):
    id: str
    last_updated_date: datetime
    def __init__(self, id: str):
        self.id: str = id
        super().__init__()
