# 📘 Google Engineering Practices — Core Code Review Rules

This module encapsulates Google's official Code Review standards (from [google.github.io/eng-practices](https://google.github.io/eng-practices/review/)).
Any automated review produced by this system MUST strictly adhere to these principles.

---

## 1. The Standard of Code Review

> **"In general, reviewers should favor approving a PR once it is in a state where it definitely improves the overall code health of the system, even if the PR isn't perfect."**

- **Code Health Over Perfection**: Do NOT block PRs seeking theoretical perfection. If the PR makes the codebase better, approve it.
- **Mentoring Opportunity**: Reviews are not just gates; they are opportunities to share knowledge. Explain *why* an alternative is preferred.
- **Maintain Consistency**: Respect existing conventions in the repo unless there is an architectural initiative to modernize them.

---

## 2. The 10-Point Review Checklist

Every PR must be evaluated against these 10 aspects:

| # | Aspect | What to Verify |
|:--|:-------|:---------------|
| 1 | **Design** | Does the change fit into the overall system architecture? Are interactions clean? |
| 2 | **Functionality** | Does this change actually do what the author intended? Are edge cases handled? |
| 3 | **Complexity** | Is the code overly clever? Could another engineer understand this in 6 months? |
| 4 | **Tests** | Are automated tests included? Do they test behavior or just implementation mock details? |
| 5 | **Naming** | Are variable, class, function, and file names self-explanatory and clear? |
| 6 | **Comments** | Do comments explain **WHY**, not what? Is commented-out code eliminated? |
| 7 | **Style** | Does it follow the language and team's style guides? |
| 8 | **Documentation** | Are relevant docs, READMEs, or OpenAPI specs updated? |
| 9 | **Every Line** | Did you inspect critical lines (not just skim the PR description)? |
| 10 | **Context** | Are you looking at the surrounding context, not just the isolated diff? |

---

## 3. How to Write Review Comments

- **Be Courteous & Constructive**: Respect the developer. Critique the *code*, not the *person*.
  - ❌ *"Why did you write such a slow query?"*
  - ✅ *"This query in the loop might trigger an N+1 issue on large datasets. Would `select_related('order')` help here?"*
- **Explain the "WHY"**: Always explain the rationale behind a requested change.
- **Provide Actionable Solutions**: Use GitHub Suggestion blocks (` ```suggestion `) whenever possible so the author can apply the fix in one click.
- **Distinguish Mandatory from Optional**:
  - `🔴 Critical`: Must fix before merge (security, data loss, crash, severe performance).
  - `🟡 Major`: Strongly recommended (bad design, missing null safety, unhandled error).
  - `🟢 Minor`: Improvements, cleanup, nice-to-have.
  - `Nit:`: Minor style or naming preference (author can ignore or accept).

---

## 4. Automatic Verdict Logic

| Verdict | Condition |
|:--------|:----------|
| 🟢 **APPROVE** | No 🔴 Critical and ≤ 1 🟡 Major issues. Code improves overall health. |
| 🟡 **COMMENT** | No 🔴 Critical, but has ≥ 2 🟡 Major issues. Review/changes recommended before merge. |
| 🔴 **REQUEST_CHANGES** | Has at least ONE 🔴 Critical issue. Merge is blocked until resolved. |
