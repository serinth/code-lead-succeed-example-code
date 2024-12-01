from typing import List, Dict, Any, Optional
from google.cloud import bigquery
from google.api_core import exceptions
from loguru import logger

def ensure_dataset_exists(client: bigquery.Client, project_id: str, dataset_id: str, location: str = "US") -> bigquery.Dataset:
    """
    Checks if a dataset exists, creates it if it doesn't.
    
    Args:
        client: BigQuery client
        dataset_id: ID of the dataset to check/create
        location: Geographic location of the dataset
        
    Returns:
        The dataset object
    """
    dataset_ref = client.dataset(project=project_id, dataset_id=dataset_id)
    
    try:
        dataset = client.get_dataset(dataset_ref)
    except exceptions.NotFound:
        logger.warning(f"Dataset id: {dataset_id} not found at location: {location}. Creating...")
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = location
        dataset = client.create_dataset(dataset)
        logger.warning("Done.")
        
    return dataset
