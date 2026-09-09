# 🤖 PR-Agent & Antigravity Auto-Review System

> Hệ thống tự động review Pull Request cho **clickessms** (Django + React monorepo).  
> Nền tảng: **[Google Engineering Practices](https://google.github.io/eng-practices/review/)** + kiến trúc **[PR-Agent](https://github.com/the-pr-agent/pr-agent)** + **Antigravity AI** (Google Ultra).

---

## ⚙️ Yêu Cầu Tối Thiểu

| Mục | Yêu Cầu |
|:----|:---------|
| **Hệ điều hành** | macOS 12+, Linux Ubuntu 20+, Windows 10+ (WSL) |
| **Python** | 3.9+ (trên Mac M-series: `/opt/homebrew/bin/python3`) |
| **GitHub CLI** | `gh` 2.0+ — đã chạy `gh auth login` với quyền `repo` |
| **Antigravity IDE** | Bản mới nhất — dùng Google Ultra quota để review AI sâu nhất |
| **cloudflared** | Tuỳ chọn — chỉ cần cho chế độ Webhook + Tunnel |

> **Máy người khác vẫn dùng được:** Bot tự động detect user hiện tại qua `gh api user`.  
> Mỗi người chỉ cần `gh auth login` bằng tài khoản GitHub của mình là đủ.

### Kiểm Tra Nhanh
```bash
python3 --version   # Python 3.x.x
gh auth status      # Logged in as <your-username>
```

---

## 🛠️ Cài Đặt

### 1. Clone repository
```bash
git clone git@github.com:minhhieu04/auto-review-pr-skill.git
```
> Nếu đang trong project clickessms với Antigravity IDE, `.agent/skills/auto-review-pr/` đã có sẵn.

### 2. Cài GitHub CLI và đăng nhập
```bash
brew install gh
gh auth login
```

### 3. Cài cloudflared (chỉ cần Webhook Tunnel)
```bash
brew install cloudflared
```

### 4. Cấu hình `bot/bot_config.json`
```json
{
  "org": "TEN_ORG_GITHUB",
  "repos": { "be": "TEN_REPO_BACKEND", "fe": "TEN_REPO_FRONTEND" },
  "monitored_repos": ["TEN_ORG/TEN_REPO_BACKEND", "TEN_ORG/TEN_REPO_FRONTEND"],
  "poll_interval_seconds": 60,
  "webhook": { "port": 8765 }
}
```

---

## 🧠 Bộ Skill AI Sử Dụng

Hệ thống kích hoạt nhiều specialized skills theo 3 tầng:

### Tier 1 — Luôn Kích Hoạt (Core Review)

| Skill | Vai Trò |
|:------|:--------|
| `code-review` | Reviewer chính — 6 trụ cột: Architecture, Quality, Security, Performance, Testing, Docs |
| `refactoring-expert` | Phát hiện code smells, hàm dài, cyclomatic complexity cao |
| `testing-expert` | Đánh giá test coverage, mock strategy, flaky patterns |
| `auth-expert` | Rà soát bảo mật endpoints, JWT, permissions, RBAC |
| `defense-in-depth` | Kiểm tra validation đa tầng (API → Logic → DB) |
| `testing-anti-patterns` | Phát hiện test rác: mock behavior thay vì real code |
| `verification-before-completion` | Gate cuối: bắt buộc có evidence trước khi approve |
| `dispatching-parallel-agents` | Điều phối multi-agent review song song |

### Tier 2 — Kích Hoạt Theo File Pattern

| Skill | Trigger (File Pattern) |
|:------|:-----------------------|
| `react-expert` | `*.jsx`, `*.tsx`, custom hooks |
| `react-performance` | Components có list/table, `useMemo`/`useCallback` |
| `typescript-expert` | `*.ts`, `*.tsx`, `tsconfig.json` |
| `state-management-expert` | Zustand stores, Redux, React Query hooks |
| `database-expert` | Django models, migrations, ORM queries |
| `postgres-expert` | Raw SQL, migrations, `JSONField` |
| `rest-api-expert` | DRF views, serializers, URL patterns |
| `css-expert` | `*.css`, `*.scss`, Tailwind classes |
| `accessibility-expert` | JSX markup mới, form/modal/dialog components |
| `playwright-expert` | `e2e/`, `*.spec.ts` |
| `github-actions-expert` | `.github/workflows/*.yml` |
| `docker-expert` | `Dockerfile*`, `docker-compose*.yml` |
| `senior-qc` | PR phức tạp (>500 lines diff) |
| `condition-based-waiting` | Phát hiện `sleep`/`setTimeout` hardcoded |

### Tier 3 — Kích Hoạt Khi Cần

| Skill | Khi Nào Dùng |
|:------|:-------------|
| `oracle` | PR có logic concurrency/race condition cực phức tạp |
| `triage-expert` | Phân loại PR theo domain ở đầu pipeline |
| `root-cause-tracing` | PR bugfix — xác minh sửa đúng gốc rễ |
| `documentation-expert` | PR có sửa docs/, README |

> Khi dùng **Antigravity Chat** (`review pr 916 be`), toàn bộ engine AI này chạy đầy đủ.  
> Bot Python (`bot/`) là lớp pre-processing — fetch diff, classify, post kết quả.

---

## 🗺️ Flow Hoạt Động

```
KÍCH HOẠT
 [ReviewBot.app]  [GitHub /review comment]  [Antigravity Chat]
       │                    │                       │
       ▼                    ▼                       ▼
────────────────────────────────────────────────────────────
 STEP 1: Thu thập dữ liệu
   gh pr view  → metadata (title, author, branch, +/- lines)
   gh pr diff  → full diff của PR
   gh api reviews → review cũ (dùng cho re-review tracking)

 STEP 2: Phân loại & định tuyến
   *.py / schema.py  → Backend Agent  (Django, N+1, Security)
   *.jsx / *.tsx     → Frontend Agent (React, CSS, Perf)
   *.yml / Dockerfile → DevOps Agent
   Lock files / Assets → SKIP

   PR Type: Feature / Bug Fix / Performance / Refactor / Tests
   Effort Score: 1-5 sao (số dòng + số file thay đổi)

 STEP 3: Phân tích (3 agents song song)
   [BE Agent]  → database-expert, auth-expert, rest-api-expert
   [FE Agent]  → react-expert, typescript-expert, css-expert
   [QA Agent]  → testing-expert, senior-qc, defense-in-depth

 STEP 4: Gửi lên GitHub
   General comment: Overview Dashboard + Findings + Checklist + Verdict
   Inline suggestions: GitHub Suggestion Blocks (1 click commit)

 STEP 5: Lưu trạng thái (state.json)
   Commit SHA → dùng cho Incremental Re-Review

 [Tùy chọn] RE-REVIEW sau khi team fix
   ✅ Resolved / ⚠️ Still Open / NEW New Issues
────────────────────────────────────────────────────────────
```

---

## 🚀 Các Chế Độ Vận Hành

### Chế Độ 1: Interactive Dashboard (Khuyên Dùng)
**Double-click** `ReviewBot.app` trên Desktop, hoặc:
```bash
python3 bot/bot.py --menu
```

```
  [BE] CLICKESSMS_BE
  [ 1]  #919  fix(PW2-1006): update password reset...  @minhhieu04  [mine]
  [ 2]  #918  feat(PW2-977): warning to calculation  @nguyennhatninh

  [FE] CLICKESSMS_FE
  [ 3]  #1463 feat(PW2-977): add warning calculation  @nguyennhatninh

  [c]  Custom PR number    [m]  Review NHIỀU PR cùng lúc
  [w]  Webhook + Tunnel    [p]  Polling Daemon
  [r]  Refresh             [q]  Thoát
```

**Tính năng:**
- Gõ `1 3 5` cách nhau bằng dấu cách → review nhiều PR cùng lúc
- Bấm `[m]` để chọn nhiều PR rồi confirm
- Nhập sai ký tự → **hỏi lại ngay**, không restart menu

---

### Chế Độ 2: Polling Daemon (Tự Động Ngầm)
```bash
python3 bot/bot.py --mode poll --interval 60
```

Hoặc bấm `[p]` trong menu → chọn 1 trong 3 chế độ:

| Option | Lọc Theo | Giải Thích |
|:-------|:---------|:-----------|
| `[1]` All open PRs | Không lọc | Quét toàn bộ PR đang mở |
| `[2]` Reviewer = tôi | `gh --reviewer @me` | PR mà team lead **request bạn review** |
| `[3]` Assignee = tôi | `gh --assignee @me` | PR được **giao cho bạn xử lý** (bạn là owner) |

> **Để dừng Polling:** nhấn `Ctrl+C` — bot sẽ dừng và quay về menu.

---

### Chế Độ 3: Webhook + Cloudflare Tunnel (Tức Thì)
```bash
python3 bot/bot.py --mode webhook --tunnel
```
→ Bot in ra: `https://xxxx.trycloudflare.com/webhook`

**Cài webhook (1 lần):**  
GitHub Repo → Settings → Webhooks → Add webhook → dán URL trên → Events: Pull requests + Issue comments

**Slash commands** trong comment PR:

| Lệnh | Tác Dụng |
|:-----|:---------|
| `/review` | Review toàn diện theo Google Standards |
| `/improve` | Tập trung vào code improvements |
| `/describe` | Tự động viết PR description |
| `/ask` | Chat về PR |

> **Lưu ý:** Cloudflare URL thay đổi mỗi lần bật lại bot (free tier) → cần cập nhật Webhook URL.

---

### Chế Độ 4: Antigravity IDE (AI Sâu Nhất)
```text
review pr 918 be
re-review pr 916 be
review pr 1463 fe
```
Chạy đầy đủ engine AI với tất cả Tier 1/2/3 skills.

---

## 📁 Cấu Trúc

```
auto-review-pr-skill/
├── SKILL.md               # Bộ não AI (prompt templates, routing, Google practices)
├── README.md              # Tài liệu này
├── bot/
│   ├── bot.py             # Entry point, CLI, routing
│   ├── bot_config.json    # Cấu hình repo, port, features
│   ├── interactive_menu.py  # Dashboard tương tác
│   ├── review_engine.py   # Rule-based scanner + GitHub poster
│   ├── polling_daemon.py  # Polling (all / reviewer / assignee mode)
│   ├── webhook_server.py  # HTTP server nhận GitHub events
│   ├── tunnel_manager.py  # Cloudflare Tunnel manager
│   └── state.py           # Lưu commit SHA (incremental re-review)
└── scripts/
    ├── review-pr.sh       # CLI shell wrapper
    └── routing.json       # File pattern → skill mapping
```

---

## 🔐 Bảo Mật

- `state.json` không được commit (đã có trong `.gitignore`)
- Token GitHub: mỗi máy dùng `gh auth login` riêng — không hardcode
- Port mặc định `8765` (tránh xung đột Docker Desktop port 8080)

---

## 🤝 Tham Khảo

- [Google Engineering Practices — Code Review](https://google.github.io/eng-practices/review/)
- [the-pr-agent/pr-agent](https://github.com/the-pr-agent/pr-agent)
