import json
import subprocess
import os
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

class ReviewEngine:
    def __init__(self, state_manager=None):
        self.state = state_manager

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

    def analyze_diff(self, diff: str) -> Dict[str, Any]:
        """Universal, stack-aware heuristic scan for bugs, N+1, security, and styling."""
        findings = []
        files = []
        current_file = ""
        current_line = 0

        for line in diff.split("\n"):
            if line.startswith("diff --git"):
                parts = line.split(" ")
                if len(parts) >= 4:
                    current_file = parts[2].replace("a/", "")
                    files.append(current_file)
            elif line.startswith("@@"):
                m = re.search(r"\+(\d+)", line)
                if m:
                    current_line = int(m.group(1))
            elif line.startswith("+") and not line.startswith("+++"):
                added = line[1:]
                file_lower = current_file.lower()
                is_test_file = any(kw in file_lower for kw in [".test.", ".spec.", "/test_", "/tests/", "_test.py"])

                # -------------------------------------------------------------
                # 1. UNIVERSAL SECURITY & SECRETS (All languages)
                # -------------------------------------------------------------
                # Hardcoded API Keys / Tokens
                if re.search(r"(api_key|token|password|secret|auth_token|private_key)\s*[:=]\s*['\"][A-Za-z0-9_\-]{10,}['\"]", added, re.IGNORECASE):
                    if not any(safe in added.lower() for safe in ["dummy", "mock", "example", "placeholder"]):
                        findings.append({
                            "file": current_file,
                            "line": current_line,
                            "severity": "🔴 Critical",
                            "level": "critical",
                            "title": "Possible Hardcoded Secret or API Key",
                            "why": "Committing credentials exposes secrets to git history. Use environment variables instead.",
                            "fix": "os.environ.get('SECRET_KEY') // or process.env.SECRET_KEY"
                        })

                # AWS Access Key Pattern
                if re.search(r"\bAKIA[0-9A-Z]{16}\b", added):
                    findings.append({
                        "file": current_file,
                        "line": current_line,
                        "severity": "🔴 Critical",
                        "level": "critical",
                        "title": "AWS Access Key Exposed",
                        "why": "Plaintext AWS Access Key detected. Revoke and rotate immediately.",
                        "fix": "Use AWS IAM roles or secrets manager"
                    })

                # Private Key Blocks
                if "BEGIN RSA PRIVATE KEY" in added or "BEGIN OPENSSH PRIVATE KEY" in added or "BEGIN PRIVATE KEY" in added:
                    findings.append({
                        "file": current_file,
                        "line": current_line,
                        "severity": "🔴 Critical",
                        "level": "critical",
                        "title": "Private Key Exposed",
                        "why": "Cryptographic private key committed in source code.",
                        "fix": "Load private keys from secure file or key vault"
                    })

                # Disabled SSL verification
                if re.search(r"\bverify\s*=\s*False\b", added) or re.search(r"rejectUnauthorized:\s*false", added):
                    findings.append({
                        "file": current_file,
                        "line": current_line,
                        "severity": "🔴 Critical",
                        "level": "critical",
                        "title": "Disabled TLS/SSL Verification",
                        "why": "Disabling TLS certificate verification enables Man-in-the-Middle (MitM) attacks.",
                        "fix": "Enable proper CA bundle verification"
                    })

                # -------------------------------------------------------------
                # 2. PYTHON / BACKEND RULES (.py)
                # -------------------------------------------------------------
                if current_file.endswith(".py"):
                    # SQL Injection via string formatting
                    if re.search(r"\.(execute|raw)\(f['\"]", added) or re.search(r"\.(execute|raw)\(.*%\s*\(", added):
                        findings.append({
                            "file": current_file,
                            "line": current_line,
                            "severity": "🔴 Critical",
                            "level": "critical",
                            "title": "SQL Injection Risk via String Formatting",
                            "why": "Constructing SQL queries with string interpolation or f-strings bypasses parameter sanitization.",
                            "fix": "cursor.execute('SELECT ... WHERE id = %s', [param])"
                        })

                    # N+1 Queries (ORM calls in loops or resolvers)
                    if re.search(r"\.(all\(\)|filter\(|get\()\b", added):
                        if any(kw in file_lower for kw in ["schema.py", "views.py", "serializers", "services", "resolvers"]):
                            if "select_related" not in added and "prefetch_related" not in added:
                                findings.append({
                                    "file": current_file,
                                    "line": current_line,
                                    "severity": "🔴 Critical",
                                    "level": "critical",
                                    "title": "Potential N+1 Query in ORM Traversal",
                                    "why": "Accessing related models in queries without select_related() or prefetch_related() causes N additional DB roundtrips.",
                                    "fix": added.strip() + " # Use .select_related() or .prefetch_related()"
                                })

                    # Swallowed Exceptions
                    if re.search(r"except(\s+Exception)?:\s*pass\b", added.strip()):
                        findings.append({
                            "file": current_file,
                            "line": current_line,
                            "severity": "🟡 Major",
                            "level": "major",
                            "title": "Silently Swallowed Exception",
                            "why": "Broad except with 'pass' hides critical errors and makes debugging unpredictable.",
                            "fix": "except SpecificException as e:\n    logger.warning(f'Handled error: {e}')"
                        })

                    # Mutable Default Argument
                    if re.search(r"def \w+\([^)]*=\s*(\[\]|\{\})", added):
                        findings.append({
                            "file": current_file,
                            "line": current_line,
                            "severity": "🟡 Major",
                            "level": "major",
                            "title": "Mutable Default Argument in Function Definition",
                            "why": "Default mutable arguments ([] or {}) are shared across all calls, causing unexpected state retention.",
                            "fix": "def func(param=None):\n    if param is None:\n        param = []"
                        })

                    # Missing null guard in resolver/view
                    if re.search(r"def resolve_\w+\(self, info, (\w+)", added):
                        m_param = re.search(r"def resolve_\w+\(self, info, (\w+)", added)
                        param = m_param.group(1) if m_param else "param"
                        if param not in ["root", "args", "kwargs"]:
                            findings.append({
                                "file": current_file,
                                "line": current_line,
                                "severity": "🟡 Major",
                                "level": "major",
                                "title": f"Missing Null Guard for Resolver Param '{param}'",
                                "why": f"If client sends null/None for '{param}', subsequent attribute accesses will raise AttributeError.",
                                "fix": f"if not {param}:\n    return None"
                            })

                # -------------------------------------------------------------
                # 3. JAVASCRIPT / TYPESCRIPT / FRONTEND (.js, .ts, .jsx, .tsx)
                # -------------------------------------------------------------
                if any(current_file.endswith(ext) for ext in [".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte"]):
                    # Debugger statement
                    if re.search(r"\bdebugger\b;", added):
                        findings.append({
                            "file": current_file,
                            "line": current_line,
                            "severity": "🔴 Critical",
                            "level": "critical",
                            "title": "Debugger Statement in Production Code",
                            "why": "debugger; will halt execution in browser devtools in production.",
                            "fix": "// Remove debugger;"
                        })

                    # CSS sticky + overflow collision
                    if "sticky" in added and "overflow" in added:
                        findings.append({
                            "file": current_file,
                            "line": current_line,
                            "severity": "🔴 Critical",
                            "level": "critical",
                            "title": "CSS Sticky Broken by Overflow Context",
                            "why": "position: sticky stops working when an ancestor or current element has overflow: hidden/auto/scroll.",
                            "fix": "// Move overflow to scroll container, keep sticky header outside"
                        })

                    # console.log leftover (non-test files)
                    if re.search(r"\bconsole\.(log|debug)\b", added) and not is_test_file:
                        findings.append({
                            "file": current_file,
                            "line": current_line,
                            "severity": "Nit:",
                            "level": "nit",
                            "title": "Leftover console.log",
                            "why": "Per Google Style Guidelines, development logging statements should be removed before merge.",
                            "fix": "// Remove console.log"
                        })

                    # Array index as React key
                    if re.search(r"key=\{index\}|key=\{i\}|key=\{idx\}", added):
                        findings.append({
                            "file": current_file,
                            "line": current_line,
                            "severity": "🟢 Minor",
                            "level": "minor",
                            "title": "Array Index Used as React Key",
                            "why": "Using array indices as keys can cause rendering glitches and state loss when items are re-ordered or filtered.",
                            "fix": "key={item.id}"
                        })

                    # TypeScript any type abuse
                    if current_file.endswith((".ts", ".tsx")) and re.search(r":\s*any\b", added) and not is_test_file:
                        findings.append({
                            "file": current_file,
                            "line": current_line,
                            "severity": "🟢 Minor",
                            "level": "minor",
                            "title": "TypeScript 'any' Type Usage",
                            "why": "Using 'any' disables compiler type safety. Use 'unknown' or a specific interface/type.",
                            "fix": "unknown"
                        })

                # -------------------------------------------------------------
                # 4. DEVOPS & DOCKER
                # -------------------------------------------------------------
                if "dockerfile" in file_lower:
                    if re.search(r"^FROM\s+[a-zA-Z0-9_\-\./]+:latest\b", added, re.IGNORECASE):
                        findings.append({
                            "file": current_file,
                            "line": current_line,
                            "severity": "🟡 Major",
                            "level": "major",
                            "title": "Unpinned Docker Base Image (:latest)",
                            "why": "Using :latest makes builds non-reproducible. Pin to a specific version or digest.",
                            "fix": "FROM python:3.11-slim"
                        })

                current_line += 1
            elif not line.startswith("-"):
                current_line += 1

        return {"files": files, "findings": findings}

    def generate_review_markdown(self, pr: Dict[str, Any], analysis: Dict[str, Any], is_rereview: bool = False, prev_sha: Optional[str] = None) -> str:
        findings = analysis["findings"]
        crit_count = sum(1 for f in findings if f["level"] == "critical")
        major_count = sum(1 for f in findings if f["level"] == "major")
        minor_count = sum(1 for f in findings if f["level"] == "minor")
        nit_count = sum(1 for f in findings if f["level"] == "nit")
        sugg_count = sum(1 for f in findings if f["level"] == "suggestion")
        total = len(findings)

        effort = self.estimate_effort(pr.get("additions", 0), pr.get("deletions", 0), pr.get("changedFiles", 1))
        pr_type = self.detect_pr_type(pr.get("title", ""), pr.get("headRefName", ""), analysis["files"])

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
                    md.append(f"1. **`{f['file']}:{f['line']}`** — {f['title']}")
                    md.append(f"   > **Why:** {f['why']}")
                    md.append(f"   ```suggestion\n   {f['fix']}\n   ```")
            md.append("")

        # Major Issues
        if major_count > 0:
            md.append("### 🟡 Major Issues")
            for f in findings:
                if f["level"] == "major":
                    md.append(f"1. **`{f['file']}:{f['line']}`** — {f['title']}")
                    md.append(f"   > **Why:** {f['why']}")
                    md.append(f"   ```suggestion\n   {f['fix']}\n   ```")
            md.append("")

        # Minor Issues
        if minor_count > 0:
            md.append("### 🟢 Minor Issues")
            for f in findings:
                if f["level"] == "minor":
                    md.append(f"1. **`{f['file']}:{f['line']}`** — {f['title']}")
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
                    "body": f"{f['severity']} **{f['title']}**\n\n**Why:** {f['why']}\n\n```suggestion\n{f['fix']}\n```"
                })

        if inline_comments:
            payload = {
                "commit_id": commit_sha,
                "event": "COMMENT",
                "body": "🤖 Auto-Review: In-line suggestions from PR analysis",
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

        analysis = self.analyze_diff(diff)
        body = self.generate_review_markdown(pr, analysis, is_rereview=is_rereview, prev_sha=last_sha)

        print(f"📝 Posting review to GitHub ({repo} PR #{pr_number})...")
        self.post_review(repo, pr_number, commit_sha, body, analysis["findings"])

        if self.state:
            self.state.record_review(repo, pr_number, commit_sha, {
                "time": datetime.now(timezone.utc).isoformat(),
                "findings_count": len(analysis["findings"]),
                "is_rereview": is_rereview
            })

        print(f"✅ Review completed for {repo} PR #{pr_number}!")
        return {"status": "success", "findings": len(analysis["findings"]), "commit": commit_sha}
