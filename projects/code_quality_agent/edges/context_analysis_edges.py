from loguru import logger
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.output_parsers import PydanticOutputParser
from states.context_analysis_state import ContextAnalysisState, ContextAnalysisFeedback
from states.context_analysis_feedback import ContextAnalysisFeedback
from llm_parser import extract_json

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
        SystemMessage(content="""You are an experienced engineering manager conducting a data-driven analysis of developer code quality metrics.

        OBJECTIVE:
        Determine if there is sufficient context to evaluate a developer's code quality based on their PR (pull request) activity and tenure.

        INSUFFICIENT CONTEXT CRITERIA (Any of these conditions indicate insufficient context):
        1. Zero PRs in the analysis period
        2. Employee tenure of 1 month or less
        3. Employee has less PRs than the amount expected per week

        ANALYSIS REQUIREMENTS:
        - Compare actual PR count against expected PR count for the lookback period
        - Consider seniority level and tenure when evaluating PR volume expectations (higher seniority and tenure can have slightly less PRs per week than the expected amount)
        - Factor in both quantitative metrics and tenure-based context
        
        Your response must be valid JSON matching this schema:
        {format_instructions}
        
        Provide detailed, actionable analysis for each category. Ensure your response is properly formatted JSON.""".format(
            format_instructions=PydanticOutputParser(pydantic_object=ContextAnalysisFeedback).get_format_instructions()
        )),
        HumanMessage(content="""Analyze the following employee data to determine whether or not there's enough context for the manager to do a proper review of their code quality:
        Employee Level: {seniority_level}
        Employee Tenure: {tenure} months
        Expected PRs per week: {expected_prs}
        Number of PRs in period: {pr_count}
        Number of days to look back: {days_to_look_back}""".format(**input_data))
    ]
    
    return state


def process_llm_response_for_context_assessment(state: ContextAnalysisState) -> ContextAnalysisState:
    logger.debug(f"processing response, last state message is: {state.messages[-1]}")
    """Process the LLM response from the last message and return the updated state."""
    try:
        # Get the LLM's response from the last message
        last_message = state.messages[-1]
        pydantic_parser = PydanticOutputParser(pydantic_object=ContextAnalysisFeedback)
        state.analysis_feedback = pydantic_parser.parse(last_message.content)
        return state
    except Exception as e:
        logger.warning(f"Failed to process LLM response for {state.employee.id}. Perhaps the model doesn't support json system formatting? Error: {e}")
    


# Known issue about Pydantic and Command updating state: https://github.com/langchain-ai/langgraph/issues/2804
# TODO: revisit this for the next step of the graph
    # if(llm_feedback.confidence >= MIN_CONFIDENCE and
    #    not llm_feedback.has_sufficient_context and 
    #    state.employee.pr_count > 0):
    #     logger.debug(f"looking for additional context...")
    #     pr_descriptions: str = "\n".join([pr.body for pr in pr_cache[state.employee.id]])
    #     logger.debug(f"PR Descriptions: {pr_descriptions}")
    #     state.messages.append(SystemMessage(content="""
    #         Analyze the PR descriptions for any links or references to tickets 
    #         that might provide additional context about the work being done.
    #         Look for patterns like JIRA tickets (e.g., PROJ-123) or GitHub issue references (#123).
                                            
    #         PR Descriptions:
    #         {pr_descriptions}
    #     """.format({
    #         "pr_descriptions": pr_descriptions
    #     })))
    #     goto = ContextAnalyzerNode.RUN_LLM.value

    # logger.debug(f"End of response, last message is: {state.messages[-1]}")
    # logger.debug(f"Going to: {goto}")

    # return Command(
    #         update = state,
    #         goto = goto
    #     )