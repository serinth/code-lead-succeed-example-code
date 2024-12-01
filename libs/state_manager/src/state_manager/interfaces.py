from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional
from datetime import datetime, timezone

class BaseState:
    """Base class for state objects with last updated tracking"""
    last_updated_date: datetime
    def __init__(self, last_updated_date: datetime = datetime.now(timezone.utc).isoformat()):
        self.last_updated_date = last_updated_date

T = TypeVar('T', bound=BaseState)

class StateManager(ABC, Generic[T]):
    """
    Generic interface for managing state persistence.
    Implementations can store state in various backends like GCP buckets, databases etc.
    
    Type parameter T represents the type of state object being stored/retrieved.
    Must be a subclass of BaseState.
    """
    
    @abstractmethod
    def save_state(self, state: T) -> None:
        """
        Saves the current state.
        
        Args:
            state: The state object to persist
        """
        pass
    
    @abstractmethod 
    def get_state(self) -> Optional[T]:
        """
        Retrieves the current state if it exists.
        
        Returns:
            The state object if it exists, None otherwise
        """
        pass
    
    @abstractmethod
    def get_last_updated(self) -> Optional[datetime]:
        """
        Gets the timestamp of when the state was last updated.
        
        Returns:
            datetime of last update if state exists, None otherwise
        """
        pass
    
    @abstractmethod
    def clear_state(self) -> None:
        """
        Clears/deletes the current state.
        """
        pass
