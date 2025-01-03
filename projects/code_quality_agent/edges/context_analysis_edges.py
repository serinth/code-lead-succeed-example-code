from loguru import logger
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.output_parsers import PydanticOutputParser
from states.context_analysis_state import ContextAnalysisState
from states.context_analysis_feedback import ContextAnalysisFeedback
from llm_parser import extract_json

from datetime import datetime, timedelta
from code_analysis_tool.interfaces import SourceControlFetcher


def prepare_initial_state(state: ContextAnalysisState) -> ContextAnalysisState:
    """First node in the graph that prepares the messages for LLM."""

    input_data = {
        "seniority_level": state.employee.seniority_level,
        "tenure": state.employee.tenure_months,
        "expected_prs": state.employee.expected_prs_per_week,
        "pr_count": state.employee.pr_count,
        "days_to_look_back": state.days_to_look_back
    }
    
    state.messages = [
        SystemMessage(content="""You are an experienced and highly technical engineering manager who can code.
        You are analyzing whether or not you have enough context on a software developer to judge their code quality.
        
        Here are the heuristics where more context would be required i.e. there isn't sufficient context:
        - if there aren't any PRs
        - if the tenure is <= 1 month
        - if the number of days to look back is too short and yields 0-5 PRs

        
        Your response must be valid JSON matching this schema:
        {format_instructions}
        
        Provide detailed, actionable analysis for each category. Ensure your response is properly formatted JSON.""".format(
            format_instructions=PydanticOutputParser(pydantic_object=ContextAnalysisFeedback).get_format_instructions()
        )),
        HumanMessage(content="""Analyze the following employee data to determine whether or not there's enough context for the manager to do a proper review of their code quality:
        Employee Level: {seniority_level}
        Employee Tenure: {tenure} months
        Expected PRs (pull requests) per week: {expected_prs}
        Number of PRs in period: {pr_count}
        Number of days to look back: {days_to_look_back}""".format(**input_data))
    ]
    
    return state

def process_llm_response_for_context_assessment(state: ContextAnalysisState) -> ContextAnalysisState:
    """Process the LLM response from the last message and return the updated state."""
    try:
        # Get the LLM's response from the last message
        last_message = state.messages[-1]
        json_response = extract_json(last_message.content)
        state.analysis_feedback = PydanticOutputParser(pydantic_object=ContextAnalysisFeedback).parse(json_response)
        return state
    except Exception as e:
        logger.error(f"Failed to process LLM response: {e}")
        raise


def fetch_employee_prs(
    cvs: SourceControlFetcher,
    cvs_username: str,
    days_lookback: int = 30
) -> int:
    """Fetch PR count for an employee within the lookback period."""
    since_date = (datetime.now() - timedelta(days=days_lookback)).isoformat()
    try:
        prs = cvs.get_merged_pull_requests_for_user(
            cvs_username,
            since_date=since_date
        )
        return len(prs)
    except Exception as e:
        logger.error(f"Failed to fetch employee PRs: {e}")
        raise