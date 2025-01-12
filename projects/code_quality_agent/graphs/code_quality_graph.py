from loguru import logger
from langgraph.graph import Graph, StateGraph
from langchain_core.messages import AIMessage
from langchain_core.language_models import BaseLanguageModel

from graphs.code_quality_nodes import CodeQualityNode
from states.code_quality_state import CodeQualityState, PRQualityAssessment
from edges.code_quality_edges import (
    prepare_pr_for_analysis,
    process_llm_response_for_code_quality_assessment
)

from code_analysis_tool.models.pull_request import PullRequest

def create_graph(llm: BaseLanguageModel, pr: PullRequest) -> Graph:
    """Create a graph for analyzing PR quality."""
    # Create graph with Pydantic state
    workflow = StateGraph(CodeQualityState, output=CodeQualityState)
    
    # Add nodes
    workflow.add_node(
        CodeQualityNode.PREPARE_PR.value,
        lambda state: prepare_pr_for_analysis(state, pr)
    )

    workflow.add_node(
        CodeQualityNode.RUN_QUALITY_ANALYSIS.value,
        lambda state: CodeQualityState(
            employee=state.employee,
            messages=state.messages + [AIMessage(content=llm.invoke(state.messages))],
            assessment=None
        )
    )
    workflow.add_node(
        CodeQualityNode.PROCESS_INITIAL_ANALYSIS.value,
        process_llm_response_for_code_quality_assessment
    )

    # Connect the nodes
    workflow.add_edge(CodeQualityNode.PREPARE_PR.value, CodeQualityNode.RUN_QUALITY_ANALYSIS.value)
    workflow.add_edge(CodeQualityNode.RUN_QUALITY_ANALYSIS.value, CodeQualityNode.PROCESS_INITIAL_ANALYSIS.value)

    # Set entry and exit points
    workflow.set_entry_point(CodeQualityNode.PREPARE_PR.value)
    workflow.set_finish_point(CodeQualityNode.PROCESS_INITIAL_ANALYSIS.value)

    try:
        return workflow.compile()
    except Exception as e:
        logger.error(f"Failed to create code quality graph: {e}")
        raise