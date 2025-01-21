from code_analysis_tool.models.pull_request import PullRequest

def merged_pr_diffs(pr: PullRequest) -> str:
    merged_diff: str = ""
    for k,v in pr.file_diffs.items():
        merged_diff += f"diff --git a/{k} b/{k}\n"
        merged_diff += v + "\n"
    return merged_diff