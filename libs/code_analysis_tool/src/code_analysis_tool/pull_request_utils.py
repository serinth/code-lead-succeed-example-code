from github.PullRequest import PullRequest
from typing import TypeAlias

filename: TypeAlias = str
diff: TypeAlias = str

def get_raw_diff(pr: PullRequest) -> dict[filename, diff]:
    """
    Get the raw diff content of a pull request organized by filename.
    
    Args:
        pr: PullRequest object
    
    Returns:
        Dictionary where keys are filenames and values are the corresponding diff content
    """
    try:
        files = pr.get_files()
        return {file.filename: file.patch for file in files if file.patch is not None}
    except Exception as e:
        raise Exception(f"Failed to get diffs for PR #{pr.number}: {str(e)}")