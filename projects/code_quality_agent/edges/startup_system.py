from typing import List, Dict
from datetime import datetime, timedelta
from code_analysis_tool.interfaces import SourceControlFetcher
from code_analysis_tool.models.pull_request import PullRequest
from loguru import logger

def fetch_employee_prs(
    cvs: SourceControlFetcher,
    pr_cache: Dict[str, List[PullRequest]],
    cvs_username: str,
    employee_email: str,
    days_lookback: int = 30
) -> None:
    """
    Fetch PR count for an employee within the lookback period and store in provided cache.
    
    Args:
        cvs: Source control fetcher instance
        pr_cache: Dictionary to store PR results
        cvs_username: Username in the source control system
        employee_email: Employee email to use as cache key
        days_lookback: Number of days to look back for PRs
    """
    since_date = (datetime.now() - timedelta(days=days_lookback)).isoformat()

    # Skip if already in cache
    if employee_email in pr_cache:
        return
    
    try:    
        # Fetch and store in provided cache
        prs: List[PullRequest] = cvs.get_merged_pull_requests_for_user(
            cvs_username,
            since_date=since_date
        )
        pr_cache[employee_email] = prs
        
    except Exception as e:
        logger.warning(f"Failed to fetch employee PRs: {e}, initializing to empty list")
        pr_cache[employee_email] = []
