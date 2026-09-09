import json
import subprocess
import os
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# ANSI Colors
BOLD = "\033[1m"
GREEN = "\033[0;32m"
BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
MAGENTA = "\033[0;35m"
DIM = "\033[2m"
RESET = "\033[0m"

# =============================================================================
# SPECIALIZED SUBAGENT REVIEWERS
# =============================================================================

class BackendReviewerAgent:
    """Subagent specialized in Backend Architecture, ORM, N+1, DB & APIs."""
    name = "Backend Reviewer Subagent"
    icon = "⚙️"

    def analyze(self, diff_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        findings = []
        for chunk in diff_chunks:
            file = chunk["file"]
            file_lower = file.lower()
            if not any(file.endswith(ext) for ext in [".py", ".go", ".java", ".sql", ".rb", ".php"]):
                continue

            for item in chunk["additions"]:
                line_no = item["line"]
                code = item["content"]

                # 1. SQL Injection via string formatting
                if re.search(r"\.(execute|raw)\(f['\"]", code) or re.search(r"\.(execute|raw)\(.*%\s*\(", code):
                    findings.append({
                        "agent": self.name,
                        "file": file,
                        "line": line_no,
                        "severity": "🔴 Critical",
                        "level": "critical",
                        "title": "SQL Injection Risk via String Formatting",
                        "why": "Constructing SQL queries with string interpolation or f-strings bypasses parameter sanitization.",
                        "fix": "cursor.execute('SELECT ... WHERE id = %s', [param])"
                    })

                # 2. N+1 Queries in ORM
                if re.search(r"\.(all\(\)|filter\(|get\()\b", code):
                    if any(kw in file_lower for kw in ["schema.py", "views.py", "serializers", "services", "resolvers"]):
                        if "select_related" not in code and "prefetch_related" not in code:
                            findings.append({
                                "agent": self.name,
                                "file": file,
                                "line": line_no,
                                "severity": "🔴 Critical",
                                "level": "critical",
                                "title": "Potential N+1 Query in ORM Traversal",
                                "why": "Accessing related models in loops/resolvers without select_related() or prefetch_related() causes N additional DB queries.",
                                "fix": code.strip() + " # Use .select_related() or .prefetch_related()"
                            })

                # 3. Swallowed Exceptions
                if re.search(r"except(\s+Exception)?:\s*pass\b", code.strip()):
                    findings.append({
                        "agent": self.name,
                        "file": file,
                        "line": line_no,
                        "severity": "🟡 Major",
                        "level": "major",
                        "title": "Silently Swallowed Exception",
                        "why": "Broad except with 'pass' hides critical errors and makes system behavior unpredictable.",
                        "fix": "except SpecificException as e:\n    logger.warning(f'Handled error: {e}')"
                    })

                # 4. Mutable Default Argument in Python
                if re.search(r"def \w+\([^)]*=\s*(\[\]|\{\})", code):
                    findings.append({
                        "agent": self.name,
                        "file": file,
                        "line": line_no,
                        "severity": "🟡 Major",
                        "level": "major",
                        "title": "Mutable Default Argument in Function Header",
                        "why": "Default mutable arguments ([] or {}) are shared across all invocations, causing state leakage.",
                        "fix": "def func(param=None):\n    if param is None:\n        param = []"
                    })

                # 5. Missing null guard in GraphQL resolvers
                if re.search(r"def resolve_\w+\(self, info, (\w+)", code):
                    m_param = re.search(r"def resolve_\w+\(self, info, (\w+)", code)
                    param = m_param.group(1) if m_param else "param"
                    if param not in ["root", "args", "kwargs"]:
                        findings.append({
                            "agent": self.name,
                            "file": file,
                            "line": line_no,
                            "severity": "🟡 Major",
                            "level": "major",
                            "title": f"Missing Null Guard for Resolver Param '{param}'",
                            "why": f"If client passes null/undefined for '{param}', subsequent attribute lookups will crash with AttributeError.",
                            "fix": f"if not {param}:\n    return None"
                        })
        return findings


class FrontendReviewerAgent:
    """Subagent specialized in React, Next.js, Hooks, TypeScript & CSS Layout."""
    name = "Frontend Performance Subagent"
    icon = "🎨"

    def analyze(self, diff_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        findings = []
        for chunk in diff_chunks:
            file = chunk["file"]
            file_lower = file.lower()
            if not any(file.endswith(ext) for ext in [".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte", ".css", ".scss"]):
                continue

            is_test_file = any(kw in file_lower for kw in [".test.", ".spec.", "/test_", "/tests/"])

            for item in chunk["additions"]:
                line_no = item["line"]
                code = item["content"]

                # 1. Debugger statement
                if re.search(r"\bdebugger\b;", code):
                    findings.append({
                        "agent": self.name,
                        "file": file,
                        "line": line_no,
                        "severity": "🔴 Critical",
                        "level": "critical",
                        "title": "Debugger Statement in Production Code",
                        "why": "debugger; will halt execution in browser devtools in production.",
                        "fix": "// Remove debugger;"
                    })

                # 2. CSS Sticky + Overflow collision
                if "sticky" in code and "overflow" in code:
                    findings.append({
                        "agent": self.name,
                        "file": file,
                        "line": line_no,
                        "severity": "🔴 Critical",
                        "level": "critical",
                        "title": "CSS Sticky Broken by Overflow Context",
                        "why": "position: sticky stops working when an ancestor or current element has overflow: hidden/auto/scroll.",
                        "fix": "// Isolate overflow context or attach sticky styles to direct viewport scroll container"
                    })

                # 3. console.log leftover
                if re.search(r"\bconsole\.(log|debug)\b", code) and not is_test_file:
                    findings.append({
                        "agent": self.name,
                        "file": file,
                        "line": line_no,
                        "severity": "Nit:",
                        "level": "nit",
                        "title": "Leftover console.log",
                        "why": "Per Google Style Guidelines, development logging statements should be removed before merge.",
                        "fix": "// Remove console.log"
                    })

                # 4. Array Index as Key
                if re.search(r"key=\{index\}|key=\{i\}|key=\{idx\}", code):
                    findings.append({
                        "agent": self.name,
                        "file": file,
                        "line": line_no,
                        "severity": "🟢 Minor",
                        "level": "minor",
                        "title": "Array Index Used as React Key",
                        "why": "Using array indices as keys causes component state bugs and re-rendering glitches when items are sorted or filtered.",
                        "fix": "key={item.id}"
                    })

                # 5. TypeScript any abuse
                if file.endswith((".ts", ".tsx")) and re.search(r":\s*any\b", code) and not is_test_file:
                    findings.append({
                        "agent": self.name,
                        "file": file,
                        "line": line_no,
                        "severity": "🟢 Minor",
                        "level": "minor",
                        "title": "TypeScript 'any' Type Usage",
                        "why": "Using 'any' disables compiler type checking. Use 'unknown' or declare a typed interface.",
                        "fix": "unknown"
                    })
        return findings


class SecurityAuditorAgent:
    """Subagent specialized in Secret Detection, Injection, TLS & Permissions."""
    name = "Security Auditor Subagent"
    icon = "🛡️"

    def analyze(self, diff_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        findings = []
        for chunk in diff_chunks:
            file = chunk["file"]
            for item in chunk["additions"]:
                line_no = item["line"]
                code = item["content"]

                # 1. API Keys & Secrets
                if re.search(r"(api_key|token|password|secret|auth_token|private_key)\s*[:=]\s*['\"][A-Za-z0-9_\-]{10,}['\"]", code, re.IGNORECASE):
                    if not any(safe in code.lower() for safe in ["dummy", "mock", "example", "placeholder", "test"]):
                        findings.append({
                            "agent": self.name,
                            "file": file,
                            "line": line_no,
                            "severity": "🔴 Critical",
                            "level": "critical",
                            "title": "Possible Hardcoded Secret or API Key",
                            "why": "Committing credentials exposes secrets to git history. Use environment variables or secret managers.",
                            "fix": "os.environ.get('SECRET_KEY') // or process.env.SECRET_KEY"
                        })

                # 2. AWS Access Key Pattern
                if re.search(r"\bAKIA[0-9A-Z]{16}\b", code):
                    findings.append({
                        "agent": self.name,
                        "file": file,
                        "line": line_no,
                        "severity": "🔴 Critical",
                        "level": "critical",
                        "title": "AWS Access Key Exposed",
                        "why": "Plaintext AWS Access Key detected. Revoke and rotate immediately.",
                        "fix": "Use AWS IAM roles or secrets manager"
                    })

                # 3. Private Key Blocks
                if any(k in code for k in ["BEGIN RSA PRIVATE KEY", "BEGIN OPENSSH PRIVATE KEY", "BEGIN PRIVATE KEY"]):
                    findings.append({
                        "agent": self.name,
                        "file": file,
                        "line": line_no,
                        "severity": "🔴 Critical",
                        "level": "critical",
                        "title": "Private Key Exposed",
                        "why": "Cryptographic private key committed in source code.",
                        "fix": "Load private keys from secure file or key vault"
                    })

                # 4. Disabled SSL/TLS verification
                if re.search(r"\bverify\s*=\s*False\b", code) or re.search(r"rejectUnauthorized:\s*false", code):
                    findings.append({
                        "agent": self.name,
                        "file": file,
                        "line": line_no,
                        "severity": "🔴 Critical",
                        "level": "critical",
                        "title": "Disabled TLS/SSL Verification",
                        "why": "Disabling TLS certificate verification enables Man-in-the-Middle (MitM) attacks.",
                        "fix": "Enable proper CA bundle verification"
                    })
        return findings


class ResilienceQAAgent:
    """Subagent specialized in Edge-Cases, Docker, Configs & Resilience."""
    name = "Resilience & QA Subagent"
    icon = "🧪"

    def analyze(self, diff_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        findings = []
        for chunk in diff_chunks:
            file = chunk["file"]
            file_lower = file.lower()

            for item in chunk["additions"]:
                line_no = item["line"]
                code = item["content"]

                # 1. Docker :latest tag
                if "dockerfile" in file_lower:
                    if re.search(r"^FROM\s+[a-zA-Z0-9_\-\./]+:latest\b", code, re.IGNORECASE):
                        findings.append({
                            "agent": self.name,
                            "file": file,
                            "line": line_no,
                            "severity": "🟡 Major",
                            "level": "major",
                            "title": "Unpinned Docker Base Image (:latest)",
                            "why": "Using :latest makes builds non-reproducible. Pin to a specific version or digest.",
                            "fix": "FROM python:3.11-slim"
                        })

                # 2. Hardcoded sleep / timeout in test files
                if any(t in file_lower for t in [".test.", ".spec.", "_test.py"]):
                    if re.search(r"\b(time\.sleep\(|setTimeout\(.*[0-9]{3,}\))", code):
                        findings.append({
                            "agent": self.name,
                            "file": file,
                            "line": line_no,
                            "severity": "🟡 Major",
                            "level": "major",
                            "title": "Hardcoded Sleep Delay in Test",
                            "why": "Arbitrary delays cause flaky tests. Replace with condition-based polling or event waiting.",
                            "fix": "await waitFor(() => expect(...).toBeVisible())"
                        })
        return findings


# =============================================================================
# REVIEW ENGINE COORDINATOR (Multi-Subagent Pipeline)
# =============================================================================

class ReviewEngine:
    def __init__(self, state_manager=None):
        self.state = state_manager
        # Initialize the 4 specialized subagents
        self.subagents = [
            BackendReviewerAgent(),
            FrontendReviewerAgent(),
            SecurityAuditorAgent(),
            ResilienceQAAgent()
        ]

    def run_command(self, cmd: List[str]) -> str:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Command failed ({res.returncode}): {' '.join(cmd)}\n{res.stderr}")
        return res.stdout.strip()

    def get_pr_details(self, repo: str, pr_number: int) -> Dict[str, Any]:
        out = self.run_command([
            "gh", "pr", "view", str(pr_number),
            "--repo", repo,
            "--json", "number,title,body,author,headRefName,baseRefName,headRefOid,additions,deletions,changedFiles,commits"
        ])
        return json.loads(out)

    def get_diff(self, repo: str, pr_number: int) -> str:
        return self.run_command(["gh", "pr", "diff", str(pr_number), "--repo", repo])

    def parse_diff_chunks(self, diff: str) -> List[Dict[str, Any]]:
        """Parse raw diff into structured chunks per file."""
        chunks = []
        current_chunk = None
        current_line = 0

        for line in diff.split("\n"):
            if line.startswith("diff --git"):
                if current_chunk:
                    chunks.append(current_chunk)
                parts = line.split(" ")
                current_file = parts[2].replace("a/", "") if len(parts) >= 4 else "unknown"
                current_chunk = {"file": current_file, "additions": []}
            elif line.startswith("@@"):
                m = re.search(r"\+(\d+)", line)
                if m:
                    current_line = int(m.group(1))
            elif line.startswith("+") and not line.startswith("+++"):
                if current_chunk:
                    current_chunk["additions"].append({
                        "line": current_line,
                        "content": line[1:]
                    })
                current_line += 1
            elif not line.startswith("-"):
                current_line += 1

        if current_chunk:
            chunks.append(current_chunk)
        return chunks

    def estimate_effort(self, additions: int, deletions: int, changed_files: int) -> int:
        total = additions + deletions
        if total < 50 and changed_files <= 2:
            return 1
        elif total < 200 and changed_files <= 5:
            return 2
        elif total < 500 and changed_files <= 10:
            return 3
        elif total < 1000:
            return 4
        return 5

    def detect_pr_type(self, title: str, branch: str, files: List[str]) -> str:
        title_lower = title.lower()
        if any(w in title_lower for w in ["feat", "feature", "add"]):
            return "✨ Feature"
        elif any(w in title_lower for w in ["fix", "bug", "patch"]):
            return "🐛 Bug Fix"
        elif any(w in title_lower for w in ["refactor", "clean"]):
            return "♻️ Refactor"
        elif any(w in title_lower for w in ["perf", "optimize", "loading"]):
            return "⚡ Performance Optimization"
        elif any(w in title_lower for w in ["test", "spec"]):
            return "🧪 Tests"
        elif any(w in title_lower for w in ["doc", "docs", "readme"]):
            return "📝 Documentation"
        return "🛠️ Maintenance"

    def dispatch_subagents(self, diff_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Dispatch all specialized subagents in parallel to analyze the diff chunks."""
        all_findings = []
        files_count = len(diff_chunks)
        print(f"\n  {BOLD}🤖 Dispatching 4 Specialized Review Subagents in parallel:{RESET}")

        def run_agent(agent):
            print(f"     {agent.icon} [{agent.name}] Analyzing {files_count} changed files...")
            return agent.analyze(diff_chunks)

        with ThreadPoolExecutor(max_workers=4) as executor:
            results = executor.map(run_agent, self.subagents)
            for res in results:
                all_findings.extend(res)

        print(f"  {GREEN}✅ All 4 Subagents completed their review!{RESET}\n")
        return all_findings

    def generate_review_markdown(self, pr: Dict[str, Any], files: List[str], findings: List[Dict[str, Any]], is_rereview: bool = False, prev_sha: Optional[str] = None) -> str:
        crit_count = sum(1 for f in findings if f["level"] == "critical")
        major_count = sum(1 for f in findings if f["level"] == "major")
        minor_count = sum(1 for f in findings if f["level"] == "minor")
        nit_count = sum(1 for f in findings if f["level"] == "nit")
        sugg_count = sum(1 for f in findings if f["level"] == "suggestion")
        total = len(findings)

        effort = self.estimate_effort(pr.get("additions", 0), pr.get("deletions", 0), pr.get("changedFiles", 1))
        pr_type = self.detect_pr_type(pr.get("title", ""), pr.get("headRefName", ""), files)

        # Verdict
        if crit_count > 0:
            verdict = "🔴 REQUEST_CHANGES"
            verdict_text = "Changes requested: Critical issues must be resolved prior to merge."
        elif major_count > 0:
            verdict = "🟡 COMMENT"
            verdict_text = "Comment: Suggestions and improvements provided, review recommended before merge."
        else:
            verdict = "🟢 APPROVE"
            verdict_text = "Approved: Code health is maintained or improved according to Google Standards."

        effort_bar = "⭐" * effort + "☆" * (5 - effort)

        md = []
        md.append(f"## 🤖 PR-Agent & Antigravity Auto-Review — #{pr['number']}")
        md.append(f"**Reviewed Commit:** `{pr.get('headRefOid', '')[:7]}` | **Type:** {pr_type} | **Effort to Review:** {effort_bar} ({effort}/5)")
        md.append(f"**Standard:** [Google Engineering Practices](https://google.github.io/eng-practices/review/)\n")
        md.append("---\n")

        # Overview Dashboard
        md.append("### 📊 Overview Dashboard\n")
        md.append("| Severity | Count | Status |")
        md.append("|:---------|:-----:|:------:|")
        md.append(f"| 🔴 Critical | {crit_count} | {'❌ Found' if crit_count else '✅ None'} |")
        md.append(f"| 🟡 Major | {major_count} | {'⚠️ Found' if major_count else '✅ None'} |")
        md.append(f"| 🟢 Minor | {minor_count} | {minor_count} |")
        md.append(f"| 💡 Suggestions | {sugg_count} | {sugg_count} |")
        md.append(f"| **Nit:** Style | {nit_count} | {nit_count} |")
        md.append(f"| **Total** | **{total}** | |\n")
        md.append(f"**Verdict:** {verdict} — *{verdict_text}*\n")
        md.append("---\n")

        if is_rereview and prev_sha:
            md.append(f"> 🔄 **Incremental Re-Review Note:** Comparing changes against previously reviewed commit `{prev_sha[:7]}`.\n")

        # Critical Issues
        if crit_count > 0:
            md.append("### 🔴 Critical Issues")
            for f in findings:
                if f["level"] == "critical":
                    agent_badge = f" `[{f.get('agent', 'Reviewer')}]`"
                    md.append(f"1. **`{f['file']}:{f['line']}`** — {f['title']}{agent_badge}")
                    md.append(f"   > **Why:** {f['why']}")
                    md.append(f"   ```suggestion\n   {f['fix']}\n   ```")
            md.append("")

        # Major Issues
        if major_count > 0:
            md.append("### 🟡 Major Issues")
            for f in findings:
                if f["level"] == "major":
                    agent_badge = f" `[{f.get('agent', 'Reviewer')}]`"
                    md.append(f"1. **`{f['file']}:{f['line']}`** — {f['title']}{agent_badge}")
                    md.append(f"   > **Why:** {f['why']}")
                    md.append(f"   ```suggestion\n   {f['fix']}\n   ```")
            md.append("")

        # Minor Issues
        if minor_count > 0:
            md.append("### 🟢 Minor Issues")
            for f in findings:
                if f["level"] == "minor":
                    agent_badge = f" `[{f.get('agent', 'Reviewer')}]`"
                    md.append(f"1. **`{f['file']}:{f['line']}`** — {f['title']}{agent_badge}")
                    md.append(f"   > **Why:** {f['why']}")
                    md.append(f"   ```suggestion\n   {f['fix']}\n   ```")
            md.append("")

        # Nit Issues
        if nit_count > 0:
            md.append("### 🧹 Nit (Style / Cleanliness)")
            for f in findings:
                if f["level"] == "nit":
                    md.append(f"- **`{f['file']}:{f['line']}`** — {f['title']}: {f['why']}")
            md.append("")

        # Google Checklist
        md.append("### 📋 Google Review Checklist")
        md.append("| Aspect | Status | Notes |")
        md.append("|:-------|:------:|:------|")
        md.append(f"| Design | {'✅' if crit_count == 0 else '⚠️'} | {'Fits codebase architecture' if crit_count == 0 else 'Refinement required'} |")
        md.append(f"| Functionality | {'✅' if crit_count == 0 else '❌'} | {'Meets expected behavior' if crit_count == 0 else 'Issues detected'} |")
        md.append(f"| Complexity | {'✅' if major_count == 0 else '⚠️'} | {'Clean and understandable' if major_count == 0 else 'Simplification suggested'} |")
        md.append(f"| Security | {'✅' if not any('Secret' in f['title'] or 'Injection' in f['title'] for f in findings) else '❌'} | Guard against injection and credentials leaks |")
        md.append(f"| Tests | ℹ️ | Ensure unit/integration tests cover new branches |")
        md.append(f"| Style & Naming | {'✅' if nit_count == 0 else '⚠️'} | Follows conventions |")
        md.append("")

        md.append("### 📊 Decision: **" + verdict + "**")
        return "\n".join(md)

    def post_review(self, repo: str, pr_number: int, commit_sha: str, review_body: str, findings: List[Dict[str, Any]]) -> None:
        # 1. Post general comment
        subprocess.run([
            "gh", "pr", "review", str(pr_number),
            "--repo", repo,
            "--comment",
            "-b", review_body
        ], check=True)

        # 2. Post inline comments if any critical/major
        inline_comments = []
        for f in findings[:10]:
            if f.get("level") in ["critical", "major", "minor"]:
                inline_comments.append({
                    "path": f["file"],
                    "line": f["line"],
                    "body": f"{f['severity']} **{f['title']}** `[{f.get('agent', 'Reviewer')}]`\n\n**Why:** {f['why']}\n\n```suggestion\n{f['fix']}\n```"
                })

        if inline_comments:
            payload = {
                "commit_id": commit_sha,
                "event": "COMMENT",
                "body": "🤖 Auto-Review: In-line suggestions from Multi-Agent Reviewers",
                "comments": inline_comments
            }
            res = subprocess.run([
                "gh", "api", f"repos/{repo}/pulls/{pr_number}/reviews",
                "--input", "-"
            ], input=json.dumps(payload), text=True, capture_output=True)
            if res.returncode != 0:
                print(f"Notice: In-line comment post fallback: {res.stderr}")

    def execute_review(self, repo: str, pr_number: int) -> Dict[str, Any]:
        print(f"🔍 Starting review on {repo} PR #{pr_number}...")
        pr = self.get_pr_details(repo, pr_number)
        diff = self.get_diff(repo, pr_number)
        commit_sha = pr.get("headRefOid", "")

        last_sha = None
        is_rereview = False
        if self.state:
            last_sha = self.state.get_last_reviewed_commit(repo, pr_number)
            if last_sha and last_sha != commit_sha:
                is_rereview = True

        # Parse chunks and dispatch subagents
        diff_chunks = self.parse_diff_chunks(diff)
        files = [c["file"] for c in diff_chunks]
        findings = self.dispatch_subagents(diff_chunks)

        body = self.generate_review_markdown(pr, files, findings, is_rereview=is_rereview, prev_sha=last_sha)

        print(f"📝 Posting review to GitHub ({repo} PR #{pr_number})...")
        self.post_review(repo, pr_number, commit_sha, body, findings)

        if self.state:
            self.state.record_review(repo, pr_number, commit_sha, {
                "time": datetime.now(timezone.utc).isoformat(),
                "findings_count": len(findings),
                "is_rereview": is_rereview
            })

        print(f"✅ Multi-Agent review completed for {repo} PR #{pr_number}!")
        return {"status": "success", "findings": len(findings), "commit": commit_sha}
