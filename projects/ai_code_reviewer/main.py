from code_reviewer import CodeReviewer
from loguru import logger
from config import settings

def main() -> None:
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
    
    print("Code Review Results:")
    for category, items in review_results.items():
        print(f"\n{category.upper()}:")
        for item in items:
            print(f"- {item}")

if __name__ == "__main__":
    main()