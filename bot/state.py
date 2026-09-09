import json
import os
from typing import Dict, Optional, Any

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")

class StateManager:
    def __init__(self, state_file: str = STATE_FILE):
        self.state_file = state_file
        self.data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save(self) -> None:
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save state: {e}")

    def get_last_reviewed_commit(self, repo: str, pr_number: int) -> Optional[str]:
        key = f"{repo}#{pr_number}"
        return self.data.get(key, {}).get("last_commit")

    def get_pr_history(self, repo: str, pr_number: int) -> Dict[str, Any]:
        key = f"{repo}#{pr_number}"
        return self.data.get(key, {})

    def record_review(self, repo: str, pr_number: int, commit_sha: str, summary: Dict[str, Any]) -> None:
        key = f"{repo}#{pr_number}"
        if key not in self.data:
            self.data[key] = {"history": []}
        
        self.data[key]["last_commit"] = commit_sha
        self.data[key]["last_review_time"] = summary.get("time")
        self.data[key]["history"].append({
            "commit": commit_sha,
            "summary": summary
        })
        self._save()
