import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any

class WebhookHandler(BaseHTTPRequestHandler):
    engine = None
    supported_commands = ["/review", "/improve", "/describe", "/ask"]

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("🤖 PR-Agent & Antigravity Webhook Bot is running!\n".encode("utf-8"))

    def do_POST(self):
        if self.path != "/webhook":
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get("Content-Length", 0))
        payload_bytes = self.rfile.read(content_length)

        try:
            payload = json.loads(payload_bytes.decode("utf-8"))
        except Exception as e:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Invalid JSON")
            return

        event_type = self.headers.get("X-GitHub-Event", "")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status": "received"}')

        # Handle events in background thread to avoid webhook timeout
        threading.Thread(target=self._process_event, args=(event_type, payload), daemon=True).start()

    def _process_event(self, event: str, payload: dict):
        if event == "ping":
            print("🏓 Received GitHub Webhook ping: connection successful!")
            return

        repo_full = payload.get("repository", {}).get("full_name")
        if not repo_full:
            return

        # Event: Pull Request
        if event == "pull_request":
            action = payload.get("action")
            pr_number = payload.get("number")
            if action in ["opened", "synchronize", "reopened"]:
                print(f"\n🚀 [Webhook] Received PR event '{action}' on {repo_full} #{pr_number}")
                if self.engine:
                    try:
                        self.engine.execute_review(repo_full, pr_number)
                    except Exception as err:
                        print(f"❌ Error during review: {err}")

        # Event: Issue Comment (Slash command in PR comments)
        elif event == "issue_comment":
            action = payload.get("action")
            if action != "created":
                return
            comment_body = payload.get("comment", {}).get("body", "").strip()
            pr_url = payload.get("issue", {}).get("pull_request")
            pr_number = payload.get("issue", {}).get("number")

            if pr_url and pr_number:
                # Check for slash commands
                first_word = comment_body.split()[0] if comment_body else ""
                if first_word in self.supported_commands:
                    print(f"\n⚡ [Webhook] Triggered command '{first_word}' on {repo_full} #{pr_number} by {payload.get('comment', {}).get('user', {}).get('login')}")
                    if self.engine:
                        try:
                            self.engine.execute_review(repo_full, pr_number)
                        except Exception as err:
                            print(f"❌ Error executing command '{first_word}': {err}")

def start_webhook_server(port: int, engine, commands: list):
    WebhookHandler.engine = engine
    WebhookHandler.supported_commands = commands
    server = HTTPServer(("0.0.0.0", port), WebhookHandler)
    print(f"📡 Webhook server listening on http://0.0.0.0:{port}/webhook")
    server.serve_forever()
