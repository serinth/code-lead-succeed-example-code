from datetime import datetime, timezone
import jsonpickle
from typing import Optional, TypeVar
from google.cloud import storage
from google.cloud.storage.blob import Blob
from google.api_core import exceptions as gcs_exceptions

from .interfaces import StateManager

T = TypeVar('T')

class GCSStateManager(StateManager[T]):
    """
    Google Cloud Storage implementation of StateManager interface.
    Stores state as JSON in a GCS bucket.
    """
    
    def __init__(self, bucket_name: str, state_path: str, state_class: type[T]) -> StateManager[T]:
        """
        Initialize GCS state manager.
        
        Args:
            bucket_name: Name of the GCS bucket
            state_path: Path/key where state will be stored in the bucket
        """
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
        self.state_path = state_path
        self.state_class = state_class
        
    def _get_blob(self) -> Blob:
        return self.bucket.blob(self.state_path)
    
    def save_state(self, state: T) -> None:
        """Save state using jsonpickle in GCS"""
        try:
            blob = self._get_blob()
            state.last_updated_date = datetime.now(timezone.utc)
            state_json = jsonpickle.encode(state)
            blob.upload_from_string(state_json)
        except (gcs_exceptions.GoogleAPIError, TypeError, AttributeError) as e:
            raise RuntimeError(f"Failed to save state to GCS: {str(e)}") from e
    
    def get_state(self) -> Optional[T]:
        """Retrieve and deserialize state from GCS using jsonpickle"""
        try:
            blob = self._get_blob()
            if not blob.exists():
                return None
                
            state_json = blob.download_as_string()
            return jsonpickle.decode(state_json)
        except gcs_exceptions.GoogleAPIError as e:
            raise RuntimeError(f"Failed to retrieve state from GCS: {str(e)}") from e
    
    def get_last_updated(self) -> Optional[datetime]:
        """Get blob's last updated timestamp"""
        try:
            blob = self._get_blob()
            if not blob.exists():
                return None
                
            return blob.updated
        except gcs_exceptions.GoogleAPIError as e:
            raise RuntimeError(f"Failed to get last updated timestamp: {str(e)}") from e
    
    def clear_state(self) -> None:
        """Delete the state blob if it exists"""
        try:
            blob = self._get_blob()
            if blob.exists():
                blob.delete()
        except gcs_exceptions.GoogleAPIError as e:
            raise RuntimeError(f"Failed to clear state: {str(e)}") from e
