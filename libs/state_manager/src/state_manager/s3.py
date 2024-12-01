import jsonpickle
import boto3
from datetime import datetime, timezone
from typing import Optional, TypeVar
from botocore.exceptions import ClientError

from .interfaces import StateManager

T = TypeVar('T')

class S3StateManager(StateManager[T]):
    """
    S3 implementation of StateManager interface.
    Stores state as JSON in an S3 bucket.
    """
    
    def __init__(self, bucket_name: str, key: str, state_class: type[T]):
        """
        Initialize S3 state manager
        
        Args:
            bucket_name: Name of the S3 bucket
            key: Key/path within the bucket where state will be stored
        """
        self.bucket = bucket_name
        self.key = key
        self.s3_client = boto3.client('s3')
        self.state_class = state_class

    def save_state(self, state: T) -> None:
        """Save state as JSON in S3"""
        state.last_updated_date = datetime.now(timezone.utc)
        try:
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=self.key,
                Body=jsonpickle.encode(state)
            )
        except ClientError as e:
            raise RuntimeError(f"Failed to save state to S3: {str(e)}")

    def get_state(self) -> Optional[T]:
        """Retrieve and deserialize state from S3"""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket,
                Key=self.key
            )
            return jsonpickle.decode(response['Body'].read().decode('utf-8'))
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            raise RuntimeError(f"Failed to retrieve state from S3: {str(e)}")

    def get_last_updated(self) -> Optional[datetime]:
        """Get last updated timestamp"""
        state = self.get_state()
        return state.last_updated_date if state else None

    def clear_state(self) -> None:
        """Delete state object from S3"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket,
                Key=self.key
            )
        except ClientError as e:
            raise RuntimeError(f"Failed to clear state from S3: {str(e)}")
