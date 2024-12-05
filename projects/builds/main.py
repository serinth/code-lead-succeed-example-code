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
    datetime_str_format = "%Y-%m-%d %H:%M:%S"
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
        
        url: str = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/workflows/{workflow_id}/runs"
        
        try:
            response: requests.Response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data: dict = response.json()
            workflow_runs: List[dict] = data.get("workflow_runs", [])
            
            if not workflow_runs:
                break
                
            for run in workflow_runs:
                try:
                    if (run["status"] == "completed" or run["status"] == "failure" or run["status"] == "cancelled") and run["conclusion"] == "success":
                        started_at: datetime = datetime.fromisoformat(run["run_started_at"].replace("Z", "+00:00"))
                        updated_at: datetime = datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00"))
                        
                        build = Build(
                            id=str(run["id"]),
                            created_at=started_at.strftime(datetime_str_format),
                            closed_at=updated_at.strftime(datetime_str_format),
                            commit=run["head_sha"],
                            branch=run["head_branch"],
                            repo=f"{repo_owner}/{repo_name}",
                            duration_secs=(updated_at - started_at).seconds
                        )
                        builds.append(build)
                except KeyError as e:
                    logger.error(f"Failed to parse workflow run data: {e}")
                    continue
            
            if len(workflow_runs) < per_page:
                break
                
            page += 1
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch workflow runs: {e}")
            break
            
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