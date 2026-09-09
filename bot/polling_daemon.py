import time
import json
import subprocess
import traceback
from typing import List, Dict, Any, Optional

class PollingDaemon:
    def __init__(self, repos: List[str], engine, state_manager,
                 interval: int = 60,
                 assigned_filter: Optional[str] = None,
                 reviewer_filter: Optional[str] = None):
        self.repos = repos
        self.engine = engine
        self.state = state_manager
        self.interval = interval
        self.assigned_filter = assigned_filter   # assignee (PR owner/giao xử lý)
        self.reviewer_filter = reviewer_filter   # reviewer (được request review)
        self.running = False

    def _fetch_prs(self, repo: str) -> List[Dict[str, Any]]:
        """Fetch open PRs, optionally filtered by reviewer or assignee."""
        cmd = [
            "gh", "pr", "list",
            "--repo", repo,
            "--state", "open",
            "--json", "number,headRefOid,updatedAt,title,assignees,reviewRequests"
        ]
        if self.assigned_filter:
            cmd += ["--assignee", self.assigned_filter]
        elif self.reviewer_filter:
            # gh pr list --reviewer @me
            cmd += ["--reviewer", self.reviewer_filter]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(res.stdout)
        except subprocess.CalledProcessError as e:
            # gh returns non-zero if no PRs found for reviewer filter — treat as empty list
            if e.returncode != 0:
                return []
            raise

    def check_repo(self, repo: str) -> None:
        try:
            prs = self._fetch_prs(repo)
            if not prs:
                return

            for pr in prs:
                num = pr["number"]
                current_sha = pr["headRefOid"]
                last_sha = self.state.get_last_reviewed_commit(repo, num)

                if last_sha != current_sha:
                    if self.reviewer_filter:
                        tag = f"[reviewer:@{self.reviewer_filter}]"
                    elif self.assigned_filter:
                        tag = f"[assignee:@{self.assigned_filter}]"
                    else:
                        tag = "[all PRs]"

                    print(f"\n  [Polling {tag}] New activity: {repo} PR #{num} — '{pr['title']}'")
                    print(f"     {last_sha[:7] if last_sha else 'None'} → {current_sha[:7]}")
                    try:
                        self.engine.execute_review(repo, num)
                    except Exception as err:
                        print(f"  [!] Error reviewing {repo} PR #{num}: {err}")
                        traceback.print_exc()
        except Exception as e:
            print(f"  [!] Polling error on {repo}: {e}")

    def start(self) -> None:
        self.running = True
        try:
            while self.running:
                for repo in self.repos:
                    self.check_repo(repo)
                time.sleep(self.interval)
        except KeyboardInterrupt:
            self.running = False
            raise  # let caller handle it
