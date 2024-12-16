import json
from typing import Dict, Optional
from langchain_ollama.llms import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.schema import BaseOutputParser
from langchain.schema.runnable import RunnableSequence
from langchain_core.runnables import RunnablePassthrough
from models import CodeReviewFeedback


class CodeReviewer:
    def __init__(self, model_name: str = "codeqwen:latest", model_base_url: str = "http://localhost:11434") -> None:
        """
        Initialize the CodeReviewer with a local Ollama model.
        
        Args:
            model_name (str): Name of the Ollama model to use (default: "codeqwen:latest")
            
        Raises:
            RuntimeError: If initialization of any component fails
        """
        self.llm: Optional[OllamaLLM] = None
        self.output_parser: Optional[BaseOutputParser] = None
        self.prompt: Optional[PromptTemplate] = None
        self.chain: Optional[RunnableSequence] = None
        
        self._initialize_components(model_name, model_base_url)

    def _initialize_components(self, model_name: str, model_base_url: str) -> None:
        """
        Initialize all components needed for the code reviewer.
        
        Args:
            model_name: Name of the Ollama model to use
            
        Raises:
            RuntimeError: If initialization of any component fails
        """
        try:
            # Initialize LLM with OllamaLLM
            self.llm = OllamaLLM(
                model=model_name,
                temperature=0.2,
                base_url=model_base_url
            )
            
            # Initialize output parser
            self.output_parser = PydanticOutputParser(pydantic_object=CodeReviewFeedback)
            
            # Create prompt template
            template = """You are an experienced code reviewer. Review the following code diff and provide specific feedback on:
            1. Readability improvements
            2. Testability improvements
            3. Security concerns and improvements

            Your response must be valid JSON matching this schema:
            {format_instructions}

            Code Diff:
            {code_diff}

            Provide detailed, actionable feedback for each category. Ensure your response is properly formatted JSON.
            Response:
            """

            self.prompt = PromptTemplate(
                template=template,
                input_variables=["code_diff"],
                partial_variables={
                    "format_instructions": self.output_parser.get_format_instructions()
                }
            )

            # Initialize the chain using RunnableSequence
            self.chain = (
                {"code_diff": RunnablePassthrough()} 
                | self.prompt 
                | self.llm 
                | self._extract_json 
                | self.output_parser
            )
            
        except Exception as e:
            # Reset any partially initialized components
            self.llm = None
            self.output_parser = None
            self.prompt = None
            self.chain = None
            raise RuntimeError(f"Failed to initialize CodeReviewer: {str(e)}")

    def _extract_json(self, text: str) -> str:
        """
        Extract JSON string from the model's response.
        Sometimes responses return stuff before the json and we specifially only want to parse json
        Args:
            text (str): Raw response from the model
            
        Returns:
            str: Extracted JSON string
        """
        start_idx = text.find('{')
        end_idx = text.rindex('}') + 1
        return text[start_idx:end_idx]

    def review_code(self, code_diff: str) -> Dict:
        """
        Analyze a code diff and return structured feedback.
        
        Args:
            code_diff (str): The code diff to analyze
            
        Returns:
            Dict: Structured feedback containing readability, testability, and security improvements
        """
        try:
            # Invoke the chain with the code diff
            parsed_response = self.chain.invoke(code_diff)
            
            return {
                "readability": parsed_response.readability,
                "testability": parsed_response.testability,
                "security": parsed_response.security
            }
        except json.JSONDecodeError as je:
            raise ValueError(f"Invalid JSON response from model: {str(je)}")
        except Exception as e:
            return {
                "error": f"Failed to analyze code: {str(e)}",
                "readability": [],
                "testability": [],
                "security": []
            }