from config import settings
from loguru import logger
from typing import List, Dict
from models.levels import SeniorityLevel
from models.employee import Employee
from graphs.context_analysis_graph import create_graph as create_context_analysis_graph
from states.context_analysis_state import ContextAnalysisState
from code_analysis_tool.github_client import GitHubClient
from langchain_ollama.llms import OllamaLLM
from edges.startup_system import fetch_employee_prs
from code_analysis_tool.models.pull_request import PullRequest




def main() -> None:
    
    github_client = GitHubClient(access_token=settings.cvs.api_key)
    
    #TODO: Get employees
    
    # Initialize cache
    pr_cache: Dict[str, List[PullRequest]] = {}

    # pr_cache[employee.id]=[]
    
    # Fetch PRs into cache
    # fetch_employee_prs(
    #     github_client,
    #     pr_cache,
    #     employee.cvs_username,
    #     employee.id
    # )
    
    # Update employee PR count from cache
    #employee.pr_count = len(pr_cache[employee.id])
    
    ## TODO: Add human entrypoint for entire graph
    ## TODO: Add agent entrypoint for entire graph

# This is the human chat path / debug testing path used via CLI. Otherwise execution should be via agent.py
if __name__ == "__main__":
    main()
