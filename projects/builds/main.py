import requests
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Sequence
from google.cloud import bigquery
from loguru import logger
from models.state import LastRunState
from state_manager.gcs import GCSStateManager
from config import settings
from models.build import Build
from setup import setup_build_table
from dataclasses import asdict
import uuid

def parse_workflow_run(run: dict, repo_owner: str, repo_name: str) -> Optional[Build]:
    """
    Parse a single workflow run into a Build object.
    
    Args:
        run: Dictionary containing workflow run data
        repo_owner: GitHub repository owner/organization
        repo_name: Name of the repository
    
    Returns:
        Build object if parsing successful, None otherwise
    """
    datetime_str_format = "%Y-%m-%d %H:%M:%S"
    
    try:
        if not (run["status"] in ["completed", "failure", "cancelled"] and run["conclusion"] == "success"):
            return None
            
        started_at: datetime = datetime.fromisoformat(run["run_started_at"].replace("Z", "+00:00"))
        updated_at: datetime = datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00"))
        
        return Build(
            id=str(run["id"]),
            created_at=started_at.strftime(datetime_str_format),
            closed_at=updated_at.strftime(datetime_str_format),
            commit=run["head_sha"],
            branch=run["head_branch"],
            status=run["status"],
            repo=f"{repo_owner}/{repo_name}",
            duration_secs=(updated_at - started_at).seconds
        )
    except KeyError as e:
        logger.error(f"Failed to parse workflow run data: {e}")
        return None

def fetch_workflow_page(
    url: str,
    headers: dict[str, str],
    params: dict[str, str]
) -> Optional[List[dict]]:
    """
    Fetch a single page of workflow runs from GitHub API.
    
    Args:
        url: GitHub API endpoint URL
        headers: Request headers
        params: Query parameters
    
    Returns:
        List of workflow runs if successful, None if failed
    """
    try:
        response: requests.Response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json().get("workflow_runs", [])
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch workflow runs: {e}")
        return None

def get_github_workflow_build_times(
    repo_owner: str, 
    repo_name: str, 
    workflow_id: str, 
    access_token: str,
    since_date: datetime
) -> List[Build]:
    """
    Gets build information for a GitHub workflow by calling the GitHub Actions API
    
    Args:
        repo_owner: GitHub repository owner/organization
        repo_name: Name of the repository
        workflow_id: ID of the workflow to get build times for
        access_token: GitHub personal access token with workflow read permissions
        since_date: DateTime to filter workflow runs from (inclusive)
    
    Returns:
        List of Build objects containing build metadata
    """
    headers: dict[str, str] = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {access_token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    url: str = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/workflows/{workflow_id}/runs"
    created_filter: str = f">={since_date.strftime('%Y-%m-%d')}"
    
    builds: List[Build] = []
    page: int = 1
    per_page: int = 100
    
    while True:
        params: dict[str, str] = {
            "created": created_filter,
            "page": str(page),
            "per_page": str(per_page)
        }
        
        workflow_runs = fetch_workflow_page(url, headers, params)
        if not workflow_runs:
            break
            
        for run in workflow_runs:
            build = parse_workflow_run(run, repo_owner, repo_name)
            if build:
                builds.append(build)
        
        if len(workflow_runs) < per_page:
            break
            
        page += 1
    
    return builds


if __name__ == '__main__':
    client = bigquery.Client()
    setup_build_table(
        client=client,
        project_id=settings.gcp.project_id,
        dataset_id=settings.gcp.dataset_id,
        table_id=settings.gcp.table_id
    )

    # Initialize GCS state manager
    state_manager: GCSStateManager = GCSStateManager(
        bucket_name=settings.bucket,
        state_path=settings.state_file_path,
        state_class=LastRunState
    )

    state: Optional[LastRunState] = state_manager.get_state()
    now: datetime = datetime.now(timezone.utc)

    if not state:
        state = LastRunState(id="initial_run")
        state.last_updated_date = now - timedelta(days=settings.initial_days_to_look_back)
        
    logger.info(f"Getting builds since: {state.last_updated_date}")

    builds: List[Build] = get_github_workflow_build_times(
        repo_owner=settings.repos.owner,
        repo_name=settings.repos.name,
        workflow_id=settings.repos.workflow_id,
        access_token=settings.access_token,
        since_date=state.last_updated_date
        )
    
    if len(builds) == 0:
        logger.info("No builds to insert")
    else:
        fully_qualified_table_id = f"{settings.gcp.project_id}.{settings.gcp.dataset_id}.{settings.gcp.table_id}"
        logger.info(f"Inserting {len(builds)} record(s) into {fully_qualified_table_id}...")
        

        errors: Sequence[dict] = client.insert_rows_json(fully_qualified_table_id, [asdict(build) for build in builds])

        if len(errors) > 0:
            raise Exception(f"Errors inserting into BigQuery: {errors}")
        logger.info(f"Finished syncing")
        client.close()
    
    state.id=str(uuid.uuid4())
    state.last_updated_date = now
    state_manager.save_state(state)