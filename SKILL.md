---
name: auto-review-pr
description: >
  Automated PR code review pipeline using multi-agent architecture.
  Dispatches specialized subagents (Backend, Frontend, Edge-Case) in parallel
  to review PRs with leader-level quality. Posts in-line GitHub Suggestion blocks.
  Use PROACTIVELY when reviewing any PR in the clickessms monorepo (BE or FE).
  Trigger: user says "review pr", "review PR #123", or uses /review-pr command.
version: 1.0.0
languages: [python, javascript, typescript, jsx, tsx]
---

# Auto-Review PR — Skill Instructions

## Overview

This skill automates the PR code review process for the `clickessms` monorepo
(Django backend + React frontend). It dispatches multiple specialized subagents
in parallel to provide comprehensive, leader-quality code reviews with in-line
GitHub Suggestion blocks.

## Review Philosophy — Google Engineering Practices

> Reference: https://google.github.io/eng-practices/review/

Every review MUST follow these principles from Google's code review guide:

### The Standard of Code Review
- **Primary purpose**: Improve overall code health of the codebase over time.
- **Favor approving** a CL once it **definitely improves** code health, even if
  it isn't perfect. There is no such thing as "perfect" code — only better code.
- **Don't block progress** over minor style nits. If a CL improves the codebase,
  approve it even with minor issues (leave them as `🟢 Minor` or `💡 Suggestion`).
- **Reject only when** the CL decreases code health (bugs, security, broken tests,
  unmaintainable complexity).

### What to Look For (Google's Checklist)
1. **Design** — Does the change fit the existing architecture? Does it belong here
   or in a library? Is it over-engineered for speculative future needs?
2. **Functionality** — Does it do what the developer intended? Think about edge
   cases, concurrency problems, and user-facing impact.
3. **Complexity** — Can it be understood quickly by other developers? "Too complex"
   = developers will introduce bugs when modifying it later.
4. **Tests** — Are tests correct, sensible, and useful? Do they test the right
   thing (behavior, not implementation)? Will they fail when the code is broken?
5. **Naming** — Do names communicate intent? Are they too long or too short?
6. **Comments** — Are comments clear and necessary? Do they explain **why**, not
   **what**? Could the code be simplified instead of commented?
7. **Style** — Follow the project's existing style guide. Pure style changes should
   not be mixed with functional changes.
8. **Documentation** — Are related docs (README, API docs) updated if needed?
9. **Every line** — Look at every line of code assigned to you. Don't just skim.
10. **Context** — Look at the whole file, not just the changed lines. The change
    might be correct in isolation but break the surrounding context.

### How to Write Review Comments (Google's Guide)
- **Be kind** — Comment on the **code**, never the **developer**.
- **Explain your reasoning** — Don't just say "this is wrong", explain **why**
  and point to documentation or evidence.
- **Balance direction vs autonomy** — Point out problems AND suggest fixes,
  but let the developer choose the approach when multiple solutions exist.
- **Encourage simplification** — Ask developers to simplify code rather than
  just explaining complexity to you.
- **Label optional comments** — Use `Nit:` prefix for minor style issues and
  `Optional:` for suggestions that aren't required for approval.

## When to Use

**Trigger conditions (ANY):**
- User says: "review pr", "review PR #NNN", "check PR", "auto review"
- User provides a PR number to review
- User asks to review a branch or diff

## Execution Flow

### Step 0: Determine Target PR

Ask or parse from user input:
- **Repo**: `clickessms_be` or `clickessms_fe` (or both if user says "review all")
- **PR Number**: The GitHub PR number
- **Org**: `deveop-com` (default)

### Step 1: Gather PR Context

```bash
# Get PR metadata
gh pr view {PR_NUMBER} --repo deveop-com/{REPO_NAME} --json number,title,body,author,headRefName,baseRefName,additions,deletions,changedFiles

# Get full diff
gh pr diff {PR_NUMBER} --repo deveop-com/{REPO_NAME}

# Get existing review comments (avoid duplicates)
gh api repos/deveop-com/{REPO_NAME}/pulls/{PR_NUMBER}/reviews
```

### Step 2: File Pattern Routing

Analyze the diff to determine which specialized skills to activate:

```
ROUTING RULES:
═══════════════════════════════════════════════════════════════
File Pattern              → Skills to Activate
═══════════════════════════════════════════════════════════════
*.py                      → database-expert, rest-api-expert, auth-expert
**/migrations/**          → postgres-expert, database-expert
**/schema.py              → database-expert (GraphQL resolvers)
**/models.py              → database-expert, postgres-expert
**/views.py, **/viewsets.* → rest-api-expert, auth-expert
**/serializers.*          → rest-api-expert

*.jsx, *.tsx              → react-expert, react-performance, accessibility-expert
*.ts, *.tsx               → typescript-expert
**/store*/*, **/hooks/*   → state-management-expert
*.css, *.scss             → css-expert
**/e2e/**, *.spec.*       → playwright-expert
*.test.*, *.spec.*        → testing-expert, testing-anti-patterns

Dockerfile*, docker-compose* → docker-expert
.github/workflows/*.yml  → github-actions-expert
═══════════════════════════════════════════════════════════════

ALWAYS ACTIVE (regardless of files):
- code-review (6-pillar framework)
- refactoring-expert (code smell detection)
- defense-in-depth (validation layers)
- verification-before-completion (evidence gate)

SKIP FILES (never review):
- package-lock.json, yarn.lock, pnpm-lock.yaml
- *.min.js, *.min.css
- *.map (source maps)
- dist/**, build/**, node_modules/**
- *.png, *.jpg, *.svg, *.ico, *.woff, *.woff2
- __pycache__/**, *.pyc
```

### Step 3: Dispatch Multi-Agent Review

Based on the files changed, dispatch UP TO 3 specialized subagents in parallel:

#### Agent 1: Backend Architecture Reviewer
**Condition:** PR contains `*.py` files
**Skills to apply:** code-review, database-expert, rest-api-expert, auth-expert, postgres-expert, refactoring-expert, defense-in-depth

**Prompt Template:**
```
You are a Senior Backend Tech Lead reviewing PR #{PR_NUMBER} in a Django/Graphene
backend project.

SKILLS TO APPLY:
- code-review: Use the 6-pillar framework (Architecture, Quality, Security, Performance, Testing, Docs)
- database-expert: Check for N+1 queries, missing select_related/prefetch_related
- rest-api-expert: Validate endpoint design, HTTP semantics, error handling
- auth-expert: Verify auth decorators on new endpoints, permission checks
- postgres-expert: Check migration safety (table locks, data loss risks)
- refactoring-expert: Detect code smells, long functions, deep nesting
- defense-in-depth: Verify validation at every layer (API → Logic → DB)

REVIEW CHECKLIST:
□ N+1 query detection in new resolvers/views
□ Missing select_related / prefetch_related on FK traversals
□ Auth decorators (@login_required, @permission_required) on new endpoints
□ Null safety — guard clauses for None parameters
□ Migration safety — no table locks, no data loss
□ Error handling — try/except with specific exceptions
□ Soft-delete awareness — filter is_deleted=False where needed
□ Input validation at API boundary
□ No hardcoded secrets/credentials
□ Function length < 30 lines, nesting < 3 levels

OUTPUT FORMAT:
For each finding, provide:
1. File path and line number
2. Severity: 🔴 Critical | 🟡 Major | 🟢 Minor | 💡 Suggestion
3. Description of the issue
4. A GitHub Suggestion block with the fix:
   ```suggestion
   // corrected code
   ```

DIFF (Python files only):
{PYTHON_DIFF}
```

#### Agent 2: Frontend Performance Reviewer
**Condition:** PR contains `*.jsx`, `*.tsx`, `*.ts`, `*.css` files
**Skills to apply:** react-expert, react-performance, typescript-expert, state-management-expert, css-expert, accessibility-expert, refactoring-expert

**Prompt Template:**
```
You are a Senior Frontend Tech Lead reviewing PR #{PR_NUMBER} in a React/Apollo
frontend project (Vite build, Apollo Client for GraphQL).

SKILLS TO APPLY:
- react-expert: Check hook rules, exhaustive-deps, stale closures, component patterns
- react-performance: Detect unnecessary re-renders, missing memoization, bundle bloat
- typescript-expert: Flag `any` usage, ensure strict type safety
- state-management-expert: Validate query caching, store architecture
- css-expert: Check layout issues (sticky, overflow, z-index stacking)
- accessibility-expert: Verify ARIA attributes, keyboard navigation, focus management
- refactoring-expert: Detect duplicated logic, long components

REVIEW CHECKLIST:
□ Hook rules: exhaustive-deps in useEffect/useCallback/useMemo
□ Stale closures: captured values in callbacks/event handlers
□ Missing cleanup in useEffect (AbortController, unsubscribe, removeEventListener)
□ Re-renders: missing React.memo on expensive children, inline objects in props
□ Bundle impact: lazy() for large imports, tree-shaking friendly imports
□ CSS: sticky + overflow conflict, z-index collisions, responsive breakpoints
□ Loading/error/empty states for all async data
□ ARIA: labels on interactive elements, role attributes on custom widgets
□ Keyboard navigation: focusable elements, tab order
□ TypeScript: no `any`, proper generic types, discriminated unions for states
□ No console.log left in production code

OUTPUT FORMAT:
Same as Backend reviewer — file:line, severity, description, suggestion block.

DIFF (Frontend files only):
{FRONTEND_DIFF}
```

#### Agent 3: Resilience & Edge-Case Reviewer
**Condition:** Always dispatched (cross-cutting concerns)
**Skills to apply:** testing-expert, testing-anti-patterns, defense-in-depth, condition-based-waiting, senior-qc

**Prompt Template:**
```
You are a Senior QA Engineer and Resilience Expert reviewing PR #{PR_NUMBER}.
Your focus is on edge cases, error paths, and test quality that other reviewers
might miss.

SKILLS TO APPLY:
- testing-expert: Evaluate test architecture, mock strategy, coverage gaps
- testing-anti-patterns: Flag tests that test mock behavior instead of real code
- defense-in-depth: Check validation at every boundary
- condition-based-waiting: Flag hardcoded delays (sleep, setTimeout) in tests
- senior-qc: Independent quality assessment with risk matrix

REVIEW CHECKLIST:
□ Error handling: every async operation has catch/error handling
□ Race conditions: concurrent operations properly guarded
□ Null/undefined: defensive checks at function boundaries
□ Empty arrays/objects: handled gracefully (not just happy path)
□ Large data: pagination, virtualization, memory limits
□ Test coverage: new code paths have corresponding tests
□ Test quality: tests verify behavior, not implementation details
□ Test anti-patterns: no testing mock behavior, no test-only production methods
□ Backward compatibility: API changes don't break existing consumers
□ Magic numbers: constants should be named and documented

OUTPUT FORMAT:
Same as other reviewers — file:line, severity, description, suggestion block.

FULL DIFF:
{FULL_DIFF}
```

### Step 4: Synthesize & Post Review

After all subagents return, synthesize their findings:

1. **Deduplicate**: Remove findings pointing to the same line with the same issue
2. **Prioritize**: Sort by severity (🔴 → 🟡 → 🟢 → 💡)
3. **Cap findings**: Max 10 in-line suggestions (avoid overwhelming the author)
4. **Determine verdict**:
   - `APPROVE` — No 🔴 Critical and no 🟡 Major issues
   - `COMMENT` — Has 🟡 Major issues but no 🔴 Critical
   - `REQUEST_CHANGES` — Has 🔴 Critical issues

#### Post General Review Summary

```bash
gh pr review {PR_NUMBER} --repo deveop-com/{REPO_NAME} --comment -F - << 'REVIEW_EOF'
## 🤖 Auto-Review Report — PR #{PR_NUMBER}

**Reviewed by:** Antigravity AI (Multi-Agent Pipeline)
**Review Agents:** {AGENT_LIST}
**Skills Applied:** {SKILL_LIST}
**Commit:** `{HEAD_COMMIT_SHA}` (latest at review time)

---

### 📊 Overview Dashboard

| Severity | Count | Status |
|:---------|:-----:|:------:|
| 🔴 Critical | {critical_count} | {✅ None / ❌ Found} |
| 🟡 Major | {major_count} | {✅ None / ⚠️ Found} |
| 🟢 Minor | {minor_count} | {ℹ️ count} |
| 💡 Suggestions | {suggestion_count} | {ℹ️ count} |
| **Nit:** Style | {nit_count} | {ℹ️ count} |
| **Total** | **{total_count}** | |

**Verdict:** {🟢 APPROVE / 🟡 COMMENT / 🔴 REQUEST_CHANGES}

---

### Summary
{1-2 sentence overview of what the PR does and overall quality assessment}

### 🔴 Critical Issues ({count})
> Must fix before merge — bugs, security vulnerabilities, data loss risks

{For each finding:}
1. **[`filename.py:42`](link)** — {Title}
   > {Explanation of WHY this is a problem, with evidence}
   ```suggestion
   {corrected code}
   ```

### 🟡 Major Issues ({count})
> Should fix — performance, missing validation, maintainability

{findings with same format}

### 🟢 Minor Issues ({count})
> Nice to have — naming, minor optimization

{findings with same format}

### 💡 Suggestions ({count})
> Optional: Alternative approaches worth considering

{findings — use "Optional:" or "Consider:" prefix}

### Nit: Style ({count})
> Nit: Non-blocking style/formatting issues

{findings — use "Nit:" prefix per Google convention}

### ✅ Strengths
> What the PR does well — always include positive feedback (Google guideline)

- {strength 1}
- {strength 2}

### 📋 Google Review Checklist

| Aspect | Status | Notes |
|:-------|:------:|:------|
| Design | ✅/⚠️/❌ | {fits architecture? over-engineered?} |
| Functionality | ✅/⚠️/❌ | {edge cases? concurrency?} |
| Complexity | ✅/⚠️/❌ | {understandable? maintainable?} |
| Tests | ✅/⚠️/❌ | {correct? sensible? coverage?} |
| Naming | ✅/⚠️/❌ | {clear intent?} |
| Comments | ✅/⚠️/❌ | {explain why, not what?} |
| Style | ✅/⚠️/❌ | {consistent with project?} |
| Documentation | ✅/⚠️/❌ | {API docs updated?} |

### 📊 Decision: **{VERDICT}**
> {Reasoning for the verdict based on Google's standard: "Does this CL improve
> the overall code health of the codebase?"}
REVIEW_EOF
```

#### Post In-line Suggestions (Top 5-10 findings)

Use `gh api` to post in-line review with GitHub Suggestion blocks.

**Comment format follows Google's guidelines:**
- Start with severity label: `🔴 Critical:`, `🟡 Major:`, `Nit:`, `Optional:`
- Explain **why** (not just what) — reference docs, evidence, or invariants
- Provide actionable fix via `suggestion` block
- Be kind — comment on the **code**, never the **developer**

```bash
gh api repos/deveop-com/{REPO_NAME}/pulls/{PR_NUMBER}/reviews \
  --input - << 'JSON_EOF'
{
  "commit_id": "{HEAD_COMMIT_SHA}",
  "event": "COMMENT",
  "body": "🤖 Auto-Review: In-line suggestions from multi-agent analysis",
  "comments": [
    {
      "path": "{FILE_PATH}",
      "line": {LINE_NUMBER},
      "body": "{SEVERITY} **{TITLE}**\n\n**Why:** {EXPLANATION — reference Google principle}\n\n**Fix:**\n```suggestion\n{SUGGESTED_CODE}\n```"
    }
  ]
}
JSON_EOF
```

### Step 5: Report to User

After posting, report back to the user with the **Overview Dashboard**:
- Total findings count by severity (table format)
- Links to the review on GitHub
- Verdict with reasoning
- Any findings that need human judgment
- Commit SHA that was reviewed (important for re-review tracking)

---

## Incremental Re-Review (After Author Fixes)

When the author fixes issues and pushes new commits, you can re-review
only the delta (new changes since last review).

### Step 0: Detect Re-Review Context

```bash
# Get the commit SHA of the last auto-review
LAST_REVIEW_SHA=$(gh api repos/deveop-com/{REPO_NAME}/pulls/{PR_NUMBER}/reviews \
  --jq '[.[] | select(.body | contains("Auto-Review Report"))] | last | .commit_id')

# Get current head commit
CURRENT_SHA=$(gh pr view {PR_NUMBER} --repo deveop-com/{REPO_NAME} --json headRefOid --jq '.headRefOid')

# If they differ, there are new commits since last review
if [ "$LAST_REVIEW_SHA" != "$CURRENT_SHA" ]; then
  echo "New commits detected since last review. Running incremental review..."
fi
```

### Step 1: Get Incremental Diff

```bash
# Diff between last reviewed commit and current head
gh api repos/deveop-com/{REPO_NAME}/compare/{LAST_REVIEW_SHA}...{CURRENT_SHA} \
  --jq '.files[] | {filename, status, patch}' > /tmp/incremental_diff.json

# OR use git diff locally
git diff {LAST_REVIEW_SHA}..{CURRENT_SHA}
```

### Step 2: Cross-Reference Previous Findings

Read previous review comments and check:
1. Which 🔴 Critical issues were **fixed** in new commits? → Mark as ✅ Resolved
2. Which 🟡 Major issues were **fixed**? → Mark as ✅ Resolved
3. Were any **new issues** introduced in the fix commits?
4. Were any previous suggestions **ignored**? → Re-flag if still relevant

### Step 3: Post Follow-Up Review

```markdown
## 🤖 Auto-Review Follow-Up — PR #{PR_NUMBER}

**Review Type:** 🔄 Incremental (re-review after fixes)
**Previous Review Commit:** `{LAST_REVIEW_SHA}`
**Current Commit:** `{CURRENT_SHA}`
**New Commits:** {count} commits since last review

---

### 📊 Updated Overview Dashboard

| Severity | Previous | Resolved | New | Remaining |
|:---------|:--------:|:--------:|:---:|:---------:|
| 🔴 Critical | {prev} | {resolved} | {new} | **{remaining}** |
| 🟡 Major | {prev} | {resolved} | {new} | **{remaining}** |
| 🟢 Minor | {prev} | {resolved} | {new} | **{remaining}** |

### ✅ Resolved Issues ({count})
- ~~`filename.py:42` — Original critical issue~~ → Fixed in `{commit_sha}`

### ⚠️ Still Open ({count})
- `filename.py:42` — {description} (not addressed in new commits)

### 🆕 New Issues ({count})
{Any new issues introduced by the fix commits}

### 📊 Updated Decision: **{VERDICT}**
```

### Re-Review Trigger Keywords

The agent should detect these and auto-switch to re-review mode:
- "re-review pr {N}"
- "review pr {N} again"
- "check if they fixed it"
- "review latest commits on pr {N}"
- "follow up review pr {N}"

---

## Important Rules

1. **NEVER auto-merge** — Only comment or approve, never merge
2. **ALWAYS post in English** — Review comments must be in English for team readability
3. **ALWAYS include positive feedback** — Mention what the PR does well (Google guideline)
4. **RESPECT the author** — Be kind, comment on CODE not the DEVELOPER (Google guideline)
5. **MAX 10 in-line suggestions** — Don't overwhelm; focus on Critical + Major
6. **VERIFY before claiming** — Run actual checks, don't guess
7. **DEDUP check** — Read existing comments before posting to avoid duplicates
8. **Context matters** — Read surrounding code, not just the diff lines (Google guideline)
9. **Label comments clearly** — Use `Nit:`, `Optional:`, severity emojis (Google guideline)
10. **Favor approval** — If CL improves code health, approve even with minor issues (Google standard)
11. **Explain WHY** — Every comment must explain the reasoning, not just flag the problem
12. **Track review commit** — Always record `commit_id` to enable incremental re-review
13. **Overview Dashboard mandatory** — Every review MUST start with the severity count table

## Example Usage

```
User: review pr 916 be
Agent: Reviewing PR #916 on clickessms_be...
       → Fetching diff... 2 files changed (+51/-83)
       → Routing: Python files detected → Backend Reviewer + Edge-Case Reviewer
       → Dispatching 2 subagents...
       → 📊 Overview: 2 🔴 Critical, 1 🟡 Major, 2 🟢 Minor, 1 Nit
       → Posted review to GitHub (commit: a1fb3b6)
       → Decision: REQUEST_CHANGES (2 critical issues found)

User: review pr 1460 fe
Agent: Reviewing PR #1460 on clickessms_fe...
       → Fetching diff... 10 files changed (+764/-401)
       → Routing: JSX + CSS files → Frontend Reviewer + Edge-Case Reviewer
       → Dispatching 2 subagents...
       → 📊 Overview: 1 🔴 Critical, 3 🟡 Major, 1 🟢 Minor, 2 💡 Suggestions
       → Posted review to GitHub (commit: 7ee56a1)
       → Decision: REQUEST_CHANGES (1 critical issue found)

User: re-review pr 916 be
Agent: Incremental re-review of PR #916...
       → Last review: commit a1fb3b6
       → Current head: commit e4c8f21 (2 new commits)
       → Checking if previous issues were fixed...
       → 📊 Updated: 2 🔴→✅ Resolved, 1 🟡→✅ Resolved, 0 New issues
       → All previous issues addressed!
       → Decision: APPROVE ✅

User: review pr 100 be fe
Agent: Reviewing PR #100 on BOTH clickessms_be AND clickessms_fe...
       → [Parallel review of both repos]
```
