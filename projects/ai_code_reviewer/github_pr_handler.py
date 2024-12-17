from loguru import logger
import hmac
import hashlib
import asyncio
from typing import Dict, Any
from github import Github
from github.Auth import Token
from code_reviewer import CodeReviewer
from config import settings

class GitHubPRHandler:
    def __init__(self, github_token: str, webhook_secret: str) -> None:
        self.github = Github(auth=Token(github_token))
        self.webhook_secret = webhook_secret.encode()
        self.code_reviewer = CodeReviewer(model_name=settings.llm.model)
        # Track running tasks
        self.running_tasks: Dict[int, asyncio.Task] = {}

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        try:
            expected_signature = "sha256=" + hmac.new(
                self.webhook_secret,
                payload,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False

    async def process_pr(self, payload: Dict[Any, Any]) -> None:
        """Asynchronous method to process the PR"""
        try:
            pr_number = payload["pull_request"]["number"]
            repo_full_name = payload["repository"]["full_name"]
            
            # Add initial comment to indicate processing has started
            repo = self.github.get_repo(repo_full_name)
            pr = repo.get_pull(pr_number)
            await pr.create_issue_comment("🔍 Code review in progress... Please wait.")
            
            # Get the diff
            diff = pr.get_files()
            
            all_feedback = []
            for file in diff:
                review_results = self.code_reviewer.review_code(file.patch)
                
                formatted_review = f"### Code Review for `{file.filename}`\n\n"
                for category, items in review_results.items():
                    formatted_review += f"\n#### {category.upper()}:\n"
                    for item in items:
                        formatted_review += f"- {item}\n"
                
                all_feedback.append(formatted_review)
            
            # Post the final review comment
            await pr.create_issue_comment("\n\n".join(all_feedback))
            
        except Exception as e:
            logger.error(f"Error processing PR: {e}")
            # Try to post error message to PR
            try:
                await pr.create_issue_comment(f"❌ An error occurred during code review: {str(e)}")
            except Exception as comment_error:
                logger.error(f"Failed to post error comment: {comment_error}")
        finally:
            # Clean up the task reference
            if pr_number in self.running_tasks:
                del self.running_tasks[pr_number]

    async def handle_pr(self, payload: Dict[Any, Any]) -> None:
        """Create an async task for PR processing"""
        try:
            pr_number = payload["pull_request"]["number"]
            
            # Cancel existing task if there is one
            existing_task = self.running_tasks.get(pr_number)
            if existing_task and not existing_task.done():
                existing_task.cancel()
                try:
                    await existing_task
                except asyncio.CancelledError:
                    pass
            
            # Create new task
            task = asyncio.create_task(self.process_pr(payload))
            self.running_tasks[pr_number] = task
            
        except Exception as e:
            logger.error(f"Error creating PR processing task: {e}")
            raise
