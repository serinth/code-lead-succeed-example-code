from enum import Enum

class CodeQualityNode(Enum):
    PREPARE_PR = "code_agent_prepare_pr"
    RUN_QUALITY_ANALYSIS = "code_agent_run_quality_analysis"
    PROCESS_INITIAL_ANALYSIS = "code_agent_process_initial_analysis"
