from enum import Enum
from typing import Optional
from loguru import logger
from langgraph.graph import Graph, StateGraph
from langchain_core.messages import AIMessage
from langchain_anthropic import ChatAnthropic
from langchain_ollama.llms import OllamaLLM
from states.context_analysis_state import ContextAnalysisState
from edges.context_analysis_edges import (
    prepare_initial_state,
    process_llm_response_for_context_assessment
)


class ContextAnalyzerNode(Enum):
    PREPARE_INITIAL_STATE = "ctx_agent_prepare_initial_state"
    RUN_LLM = "ctx_agent_run_llm"
    PROCESS_LLM_RESPONSE = "ctx_agent_process_context_assessment"


# TODO add options to swap models from Ollama to Anthropic and OpenAI
def create_graph(model_name: str, uri: Optional[str] = None, temperature: float = 0.2) -> Graph:
    # Create graph with Pydantic state
    workflow = StateGraph(ContextAnalysisState, output=ContextAnalysisState)
    
    # Create LLM node
    llm = OllamaLLM(
        model=model_name,
        temperature=temperature,
        base_url=uri
    )
    
    # Add nodes
    workflow.add_node(ContextAnalyzerNode.PREPARE_INITIAL_STATE.value, prepare_initial_state)
    # Add LLM response to messages while preserving state
    workflow.add_node(ContextAnalyzerNode.RUN_LLM.value, lambda state: ContextAnalysisState(
        employee=state.employee,
        days_to_look_back=state.days_to_look_back,
        messages=state.messages + [AIMessage(content=llm.invoke(state.messages))],
        analysis_feedback=None
    ))
    workflow.add_node(ContextAnalyzerNode.PROCESS_LLM_RESPONSE.value, process_llm_response_for_context_assessment)
    
    # Connect the nodes
    workflow.add_edge(ContextAnalyzerNode.PREPARE_INITIAL_STATE.value, ContextAnalyzerNode.RUN_LLM.value)
    workflow.add_edge(ContextAnalyzerNode.RUN_LLM.value, ContextAnalyzerNode.PROCESS_LLM_RESPONSE.value)
    
    # Set entry and exit points
    workflow.set_entry_point(ContextAnalyzerNode.PREPARE_INITIAL_STATE.value)
    workflow.set_finish_point(ContextAnalyzerNode.PROCESS_LLM_RESPONSE.value)
    try:           
        return workflow.compile()
    except Exception as e:
        logger.error(f"Failed to create context analysis graph: {e}")
        raise