import time
import json
import subprocess
import traceback
from typing import List, Dict, Any

class PollingDaemon:
    def __init__(self, repos: List[str], engine, state_manager, interval: int = 60):
        self.repos = repos
        self.engine = engine
        self.state = state_manager
        self.interval = interval
        self.running = False

    def check_repo(self, repo: str) -> None:
        try:
            res = subprocess.run([
                "gh", "pr", "list",
                "--repo", repo,
                "--state", "open",
                "--json", "number,headRefOid,updatedAt,title"
            ], capture_output=True, text=True, check=True)
            
            prs = json.loads(res.stdout)
            for pr in prs:
                num = pr["number"]
                current_sha = pr["headRefOid"]
                last_sha = self.state.get_last_reviewed_commit(repo, num)

                if last_sha != current_sha:
                    print(f"\n🔔 [Polling] Detected new activity on {repo} PR #{num}: '{pr['title']}'")
                    print(f"   Previous commit: {last_sha[:7] if last_sha else 'None'}")
                    print(f"   Current commit : {current_sha[:7]}")
                    try:
                        self.engine.execute_review(repo, num)
                    except Exception as err:
                        print(f"❌ Error reviewing {repo} PR #{num}: {err}")
                        traceback.print_exc()
        except Exception as e:
            print(f"⚠️ [Polling] Error checking {repo}: {e}")

    def start(self) -> None:
        self.running = True
        print(f"🔄 Polling Daemon started. Checking repos every {self.interval}s:")
        for r in self.repos:
            print(f"   - {r}")
        print("💡 Press Ctrl+C to stop.\n")

        try:
            while self.running:
                for repo in self.repos:
                    self.check_repo(repo)
                time.sleep(self.interval)
        except KeyboardInterrupt:
            print("\n⏹️ Polling Daemon stopped by user.")
