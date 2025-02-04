import re


def extract_json_string(ai_message_content: str) -> str:
    """
    Extracts the raw JSON string from an AIMessage.content string.

    Args:
        ai_message_content (str): The raw content from AIMessage.

    Returns:
        str: Extracted JSON string.
    """
    json_match = re.search(r'```json\s*(.*?)\s*```', ai_message_content, re.DOTALL)

    if not json_match:
        raise ValueError("No valid JSON found in the AIMessage content.")

    return json_match.group(1)
