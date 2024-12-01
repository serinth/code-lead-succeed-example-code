import requests
from datetime import datetime, timezone
from typing import Optional, List
from google.cloud import storage
from loguru import logger
import json
from models.state import LastRunState
from state_manager.gcs import GCSStateManager
from state_manager.interfaces import StateManager
from config import settings

def get_github_workflow_build_times(
    repo_owner: str, 
    repo_name: str, 
    workflow_id: str, 
    access_token: str,
    since_date: datetime
) -> List[float]:
    """
    Gets build times for a GitHub workflow by calling the GitHub Actions API
    
    Args:
        repo_owner: GitHub repository owner/organization
        repo_name: Name of the repository
        workflow_id: ID of the workflow to get build times for
        access_token: GitHub personal access token with workflow read permissions
        since_date: DateTime to filter workflow runs from (inclusive)
    
    Returns:
        List of build durations in seconds
    """
    headers: dict[str, str] = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {access_token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    url: str = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/workflows/{workflow_id}/runs"
    
    response: requests.Response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    try:
        workflow_runs: List[dict] = response.json()["workflow_runs"]
        build_times: List[float] = []
        
        for run in workflow_runs:
            # Only include completed runs that are newer than since_date
            if run["status"] == "completed" and run["conclusion"] == "success":
                started_at: datetime = datetime.fromisoformat(run["run_started_at"].replace("Z", "+00:00"))
                
                if started_at >= since_date:
                    updated_at: datetime = datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00"))
                    duration: float = (updated_at - started_at).total_seconds()
                    build_times.append(duration)
                
        return build_times
    except KeyError as e:
        logger.error(f"Failed to parse GitHub API response: {e}")
        return []



if __name__ == '__main__':
    # Initialize GCS state manager
    state_manager: GCSStateManager = GCSStateManager(
        bucket_name=settings.bucket,
        state_path=settings.state_file_path,
        state_class=LastRunState
    )

    state: Optional[LastRunState] = state_manager.get_state()
    
    if state:
        logger.info(f"Last sync at: {state.last_updated_date}, updating it...")
        state.last_updated_date = datetime.now(timezone.utc).isoformat()
        state_manager.save_state(state)
        pass
    else:
        logger.info(f"No last run state found, making one up")
        state = LastRunState(id="test_run_id")
        #logger.info(f"state before save_state(): {json.dumps(state, default=str)}")
        state_manager.save_state(state)