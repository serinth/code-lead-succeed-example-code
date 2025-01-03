from config import settings
from loguru import logger
from models.levels import SeniorityLevel
from models.employee import Employee
from graphs.context_analysis_graph import create_graph as create_context_analysis_graph
from states.context_analysis_state import ContextAnalysisState
from code_analysis_tool.github_client import GitHubClient


def main() -> None:
    try:
        github_client = GitHubClient(access_token=settings.cvs.api_key)
        
        employee = Employee(
            id="serinth@gmail.com",
            cvs_username="serinth",
            seniority_level=SeniorityLevel.SENIOR.value,
            expected_prs_per_week=3,
            tenure_months=6,
            pr_count=0
        )

        # Initialize state using Pydantic model
        initial_state = ContextAnalysisState(
            employee=employee,
            days_to_look_back=30,
            messages=[],  # Initialize empty messages
            analysis_feedback=None  # Initialize feedback as None
        )
        
        # Create and run the graph
        app = create_context_analysis_graph(
            model_name = settings.llm.contextualizer.model_name, 
            uri = settings.llm.contextualizer.uri
        )
        final_state = app.invoke(initial_state)
        
        # Convert final_state to GraphState if needed
        if not isinstance(final_state, ContextAnalysisState):
            final_state = ContextAnalysisState(**final_state)
        
        # Process results
        logger.info("Analysis complete")
        logger.info(final_state.analysis_feedback)
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
