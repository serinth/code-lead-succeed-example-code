from typing import List, Dict, Any, Optional
from google.cloud import bigquery
from google.api_core import exceptions
from loguru import logger

def ensure_table_exists(
    client: bigquery.Client,
    project_id: str,
    dataset_id: str,
    table_id: str,
    schema: List[bigquery.SchemaField],
    partition_type: bigquery.TimePartitioningType = bigquery.TimePartitioningType.DAY,
    partition_by: Optional[str] = None,
    clustering_fields: Optional[List[str]] = None
) -> bigquery.Table:
    """
    Checks if a table exists in the dataset, creates it if it doesn't.
    
    Args:
        client: BigQuery client
        dataset_id: ID of the dataset containing the table
        table_id: ID of the table to check/create
        schema: List of SchemaField objects defining the table schema
        clustering_fields: Optional list of fields to cluster by
        partition_by: Optional field name to partition by (DAY)
        
    Returns:
        The table object
    """
    table_ref = client.dataset(project=project_id, dataset_id=dataset_id).table(table_id)
    try:
        table = client.get_table(table_ref)
    except exceptions.NotFound:
        logger.warning(f"Table {table_id} not found in Dataset Id: {dataset_id}. Creating...")
        table = bigquery.Table(table_ref, schema=schema)
        
        if clustering_fields:
            table.clustering_fields = clustering_fields
        if partition_by:
            table.time_partitioning = bigquery.TimePartitioning(
                type_=partition_type,
                field=partition_by
            )
            
        table = client.create_table(table)
        logger.warning("Done.")
        
    return table
