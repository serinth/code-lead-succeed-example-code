def extract_json(text: str) -> str:
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
