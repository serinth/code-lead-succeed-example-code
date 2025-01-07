from enum import Enum

class ContextAnalyzerNode(Enum):
    PREPARE_INITIAL_STATE = "ctx_agent_prepare_initial_state"
    RUN_LLM = "ctx_agent_run_llm"
    PROCESS_LLM_RESPONSE = "ctx_agent_process_context_assessment"
