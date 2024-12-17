from code_reviewer import CodeReviewer
from loguru import logger
from config import settings
from github_app import app
import sys

def run_example() -> None:
    try:
        # Example usage
        code_reviewer = CodeReviewer(model_name=settings.llm.model)
        
        sample_diff = """
        @@ -1,5 +1,7 @@
        -def process_user_input(data):
        +def process_user_input(data: dict) -> bool:
             try:
        -        result = eval(data['command'])
        -        return result
        +        if 'command' in data:
        +            result = eval(data['command'])  # nosec
        +            return bool(result)
        +        return False
             except:
                 return False
        """
        
        review_results = code_reviewer.review_code(sample_diff)
        
        logger.info("Code Review Results:")
        for category, items in review_results.items():
            logger.info(f"\n{category.upper()}:")
            for item in items:
                logger.info(f"- {item}")
    except Exception as e:
        logger.error(f"Error running example: {e}")
        raise

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "example":
        run_example()
    else:
        app.run(host="0.0.0.0", port=8000)