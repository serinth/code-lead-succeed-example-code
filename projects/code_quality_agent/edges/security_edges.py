from loguru import logger
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.output_parsers import PydanticOutputParser
from code_analysis_tool.models.pull_request import PullRequest
from states.base_evaluation import BaseEvaluation
from states.code_quality_state import CodeQualityEvaluation
from edges.pr_utils import merged_pr_diffs
def prepare_pr_for_security_analysis(
    state: CodeQualityEvaluation,
    pr: PullRequest
) -> CodeQualityEvaluation:
    """Prepare the initial state by merging the file diffs of the PR"""
    # Initialize empty string to store merged diffs
    merged_diff = merged_pr_diffs(pr)
    
    # Add message with merged diffs for analysis
    state.messages = [
        SystemMessage(content="""You are a security expert reviewing code changes in a pull request. Analyze the provided code for potential security vulnerabilities, focusing on:
        - Input validation issues
        - Authentication/authorization flaws
        - Data exposure risks
        - Injection vulnerabilities
        - Cryptographic weaknesses
        - Hardcoded secrets
        - Insecure dependencies
        - Race conditions
        - Memory safety issues
        - Business logic flaws that could be exploited
                      
        Then provide a list of recommendations for improving the security of the code including:
        - the file name where the issue is identified,
        - the affected line numbers in the code, 
        - the code snippet of the insecure code matching the line numbers, 
        - a short description of the issue, 
        - a suggested fix for the issue.

        Your response must be valid JSON matching this schema:
        {format_instructions}                    
        """.format(format_instructions=PydanticOutputParser(pydantic_object=BaseEvaluation).get_format_instructions())),
        HumanMessage(content=f"Analyze the following pull request with id: {pr.id} for security concerns #{pr.title}:\n\n{merged_diff}")
    ]        
    return state


def fix_json_format(message) -> str:
    import re

    json_str = message.content.replace("```json", "").replace("```", "")

    fixed_str = re.sub(r"{{", r"{{{{", json_str)
    fixed_string = re.sub(r"}}", r"}}}}", fixed_str)
    return fixed_string


def process_llm_response_for_security_assessment(state: CodeQualityEvaluation) -> CodeQualityEvaluation:
    """Process the LLM response from the last message and return the updated state."""
    try:
        # Get the LLM's response from the last message
        last_message = state.messages[-1]
        last_message = fix_json_format(last_message)
        pydantic_parser = PydanticOutputParser(pydantic_object=BaseEvaluation)
        evaluation = pydantic_parser.parse(last_message)
        state.evaluation = evaluation
        logger.debug(f"Security evaluation: {evaluation}")
    except Exception as e:
        raise ValueError(f"Failed to process LLM response for {state.employee_id}. Perhaps the model doesn't support json system formatting? Error: {e}")

    return state
