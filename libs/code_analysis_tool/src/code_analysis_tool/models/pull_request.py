from datetime import datetime
from typing import Optional

from code_analysis_tool.models.user import User
from code_analysis_tool.models.repository import Repository
from loguru import logger

class PullRequest:
    def __init__(self, 
                 id: str,
                 number: int,
                 title: str,
                 author: User,
                 repository: Repository,
                 created_at: datetime,
                 merged_at: Optional[datetime],
                 merged: bool,
                 description: Optional[str],
                 file_diffs: Optional[dict] = None,
                 _diff_loader: Optional[callable] = None
                 ) -> None:
        self.id = id
        self.number = number
        self.title = title
        self.author = author
        self.repository = repository
        self.created_at = created_at
        self.merged_at = merged_at
        self.merged = merged
        self.description = description
        self._file_diffs = file_diffs
        self._diff_loader = _diff_loader

    @property
    def file_diffs(self) -> dict:
        if self._file_diffs is None and self._diff_loader is not None:
            try:
                self._file_diffs = self._diff_loader()
            except Exception as e:
                logger.warning(f"Failed to load diffs for PR #{self.number}: {str(e)}")
                self._file_diffs = {}
        return self._file_diffs or {}