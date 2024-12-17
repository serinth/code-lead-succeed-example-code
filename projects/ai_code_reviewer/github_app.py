from quart import Quart, request
from loguru import logger
import json
import asyncio
from typing import Dict
from config import settings
from github_pr_handler import GitHubPRHandler

app = Quart(__name__)

pr_handler = GitHubPRHandler(
    github_token=settings.github.token,
    webhook_secret=settings.github.webhook_secret
)

@app.route("/webhook", methods=["POST"])
async def webhook() -> Dict[str, str]:
    try:
        # Verify the webhook signature
        signature = request.headers.get("X-Hub-Signature-256")
        if not signature:
            return {"error": "No signature provided"}, 400

        payload_body = await request.get_data()
        logger.debug(f"Raw payload: {payload_body}")
        
        if not pr_handler.verify_signature(payload_body, signature):
            return {"error": "Invalid signature"}, 401

        # Parse the webhook payload
        event_type = request.headers.get("X-GitHub-Event")

        if payload_body:
            payload = json.loads(payload_body.decode("utf-8"))
            logger.debug(f"Parsed payload: {payload}")
        else:
            logger.error("Empty payload received")
            return {"error": "Empty payload"}, 400

        # Handle ping event
        if event_type == "ping":
            return {
                "status": "success",
                "message": "Pong!",
                "zen": payload.get("zen")
            }, 200

        # Handle PR events
        if event_type == "pull_request":
            action = payload.get("action")
            if action in ["opened", "synchronize"]:
                # Create task without awaiting it
                asyncio.create_task(pr_handler.handle_pr(payload))
                return {"status": "Review started successfully"}, 202  # 202 Accepted

        logger.info(f"Ignoring event type: {event_type}")
        return {"status": "Event ignored"}, 200

    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON payload: {e}")
        logger.debug(f"Raw payload: {payload_body}")
        return {"error": "Invalid JSON payload"}, 400
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000) 