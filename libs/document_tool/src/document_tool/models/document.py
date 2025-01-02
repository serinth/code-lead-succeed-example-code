from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Callable

@dataclass
class Document:
    id: str
    title: str
    space: str
    last_modified: datetime
    url: str
    _content_loader: Optional[Callable[[], str]] = None
    _content: Optional[str] = None

    @property
    def content(self) -> str:
        """Lazy load and return the document content."""
        if self._content is None and self._content_loader is not None:
            try:
                self._content = self._content_loader()
            except Exception as e:
                raise RuntimeError(f"Failed to load document content: {str(e)}")
        return self._content or "" 