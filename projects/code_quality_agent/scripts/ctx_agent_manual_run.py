# For manual testing of the context analysis graph

from config import settings
from loguru import logger
from models.levels import SeniorityLevel
from models.employee import Employee
from graphs.context_analysis_graph import create_graph as create_context_analysis_graph
from states.context_analysis_state import ContextAnalysisState
from langchain_ollama.llms import OllamaLLM


def main() -> None:
    employee = Employee(
        id="serinth@gmail.com",
        cvs_username="serinth",
        seniority_level=SeniorityLevel.SENIOR.value,
        expected_prs_per_week=3,
        tenure_months=1,
        pr_count=0
    )

    # Initialize state using Pydantic model
    initial_state = ContextAnalysisState(
        employee=employee,
        days_to_look_back=30,
        messages=[],  # Initialize empty messages
        analysis_feedback=None  # Initialize feedback as None
    )

    try:
        # TODO, modular LLM usage here.
        
        # Create LLM node
        llm = OllamaLLM(
            model=settings.llm.contextualizer.model_name,
            temperature=settings.llm.contextualizer.temperature,
            base_url=settings.llm.contextualizer.uri
        )
        # Create and run the graph
        app = create_context_analysis_graph(
            llm=llm
        )
        final_state = app.invoke(initial_state)
        final_state = ContextAnalysisState(**final_state)
        
        # Process results
        logger.info("Analysis complete")
        logger.info(final_state.analysis_feedback)


        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()