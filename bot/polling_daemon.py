import time
import json
import subprocess
import traceback
from typing import List, Dict, Any, Optional

class PollingDaemon:
    def __init__(self, repos: List[str], engine, state_manager,
                 interval: int = 60, assigned_filter: Optional[str] = None):
        self.repos = repos
        self.engine = engine
        self.state = state_manager
        self.interval = interval
        self.assigned_filter = assigned_filter  # None = all PRs, str = only PRs assigned to this user
        self.running = False

    def _fetch_prs(self, repo: str) -> List[Dict[str, Any]]:
        cmd = [
            "gh", "pr", "list",
            "--repo", repo,
            "--state", "open",
            "--json", "number,headRefOid,updatedAt,title,assignees"
        ]
        if self.assigned_filter:
            cmd += ["--assignee", self.assigned_filter]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(res.stdout)

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
                    mode_tag = f"[assigned:@{self.assigned_filter}]" if self.assigned_filter else "[all PRs]"
                    print(f"\n🔔 [Polling {mode_tag}] New activity on {repo} PR #{num}: '{pr['title']}'")
                    print(f"   Previous: {last_sha[:7] if last_sha else 'None'} → Current: {current_sha[:7]}")
                    try:
                        self.engine.execute_review(repo, num)
                    except Exception as err:
                        print(f"❌ Error reviewing {repo} PR #{num}: {err}")
                        traceback.print_exc()
        except Exception as e:
            print(f"⚠️  [Polling] Error checking {repo}: {e}")

    def start(self) -> None:
        self.running = True
        mode_label = f"assigned to @{self.assigned_filter}" if self.assigned_filter else "all open PRs"
        print(f"🔄 Polling Daemon started — mode: {mode_label} — interval: {self.interval}s")
        for r in self.repos:
            print(f"   - {r}")
        print("   Ctrl+C to stop.\n")

        try:
            while self.running:
                for repo in self.repos:
                    self.check_repo(repo)
                time.sleep(self.interval)
        except KeyboardInterrupt:
            print("\n⏹️  Polling Daemon stopped by user.")
