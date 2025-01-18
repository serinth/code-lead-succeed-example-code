from typing import Callable, TypeVar, Type
from enum import Enum
from pydantic import BaseModel
from langgraph.graph import Graph, StateGraph
from langchain_core.messages import AIMessage
from langchain_core.language_models import BaseLanguageModel
from code_analysis_tool.models.pull_request import PullRequest
from loguru import logger
# Generic type for the state
T = TypeVar('T', bound=BaseModel)

class ANALYSIS_NODES(Enum):
    PREPARE_PR = "PREPARE_PR"
    RUN_ANALYSIS = "RUN_ANALYSIS"
    PROCESS_ANALYSIS = "PROCESS_ANALYSIS"

def create_analysis_graph(
    llm: BaseLanguageModel,
    pr: PullRequest,
    state_class: Type[T],
    prepare_function: Callable[[T, PullRequest], T],
    process_function: Callable[[T], T],
    agent_name: str
) -> Graph:
    """
    Create a reusable graph for analyzing PRs with custom state and processing functions.
    
    Args:
        llm: The language model to use for analysis
        pr: The pull request to analyze
        state_class: The Pydantic state class to use
        prepare_function: Function to prepare the PR for analysis
        process_function: Function to process the LLM response
        agent_name: Name of the agent, used to prefix the node names
    
    Returns:
        Graph: Compiled workflow graph
    """
    prepare_pr_node_name = agent_name + ANALYSIS_NODES.PREPARE_PR.value
    run_analysis_node_name = agent_name + ANALYSIS_NODES.RUN_ANALYSIS.value
    process_analysis_node_name = agent_name + ANALYSIS_NODES.PROCESS_ANALYSIS.value
    
        # Create graph with provided state class
    workflow = StateGraph(state_class, output=state_class)
    
    # Add nodes with custom functions
    workflow.add_node(
        prepare_pr_node_name,
        lambda state: prepare_function(state, pr)
    )

    workflow.add_node(
        run_analysis_node_name,
        lambda state: state_class.model_validate({
            **state.model_dump(),
            'messages': state.messages + [AIMessage(content=llm.invoke(state.messages))]
        })
    )

    workflow.add_node(
        agent_name + ANALYSIS_NODES.PROCESS_ANALYSIS.value,
        process_function
    )

    # Connect the nodes
    workflow.add_edge(prepare_pr_node_name, run_analysis_node_name)
    workflow.add_edge(run_analysis_node_name, process_analysis_node_name)

    # Set entry and exit points
    workflow.set_entry_point(prepare_pr_node_name)
    workflow.set_finish_point(process_analysis_node_name)

    try:
        return workflow.compile()
    except Exception as e:
        logger.error(f"Failed to create analysis graph: {e}")
        raise