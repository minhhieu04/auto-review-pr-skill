# 🤖 PR-Agent & Antigravity Auto-Review System

> Hệ thống tự động review Pull Request cho dự án **clickessms** (Django + React monorepo).
> Kết hợp tiêu chuẩn **[Google Engineering Practices](https://google.github.io/eng-practices/review/)** và kiến trúc **[PR-Agent](https://github.com/the-pr-agent/pr-agent)** với Antigravity AI Agent (Google Ultra).

---

## ⚙️ Yêu Cầu Tối Thiểu

| Mục | Yêu Cầu |
|:----|:---------|
| **Hệ điều hành** | macOS 12+, Linux Ubuntu 20+, Windows 10+ (WSL) |
| **Python** | 3.9+ (`/opt/homebrew/bin/python3` trên Mac M-series) |
| **GitHub CLI** | `gh` 2.0+ — đã `gh auth login` với quyền `repo` |
| **Quyền GitHub** | Token scope: `repo`, `read:org` |
| **Antigravity IDE** | Bản mới nhất (dùng Google Ultra quota cho phân tích AI sâu) |
| **cloudflared** | Chỉ cần nếu dùng chế độ Webhook + Cloudflare Tunnel |

### Kiểm Tra Nhanh
```bash
python3 --version      # → Python 3.x.x
gh auth status         # → Logged in to github.com account xxx
```

---

## 🛠️ Cài Đặt

### Bước 1 — Clone repository
```bash
git clone git@github.com:minhhieu04/auto-review-pr-skill.git
```
> Nếu đang dùng trong project clickessms với Antigravity IDE, thư mục `.agent/skills/auto-review-pr/` đã có sẵn — bỏ qua bước này.

### Bước 2 — Cài GitHub CLI và đăng nhập
```bash
brew install gh
gh auth login
# Chọn: GitHub.com → SSH → Paste token → Done
```

### Bước 3 — Cài cloudflared (chỉ cần cho Webhook Tunnel)
```bash
# macOS
brew install cloudflared

# Linux
curl -L -o cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb
```

### Bước 4 — Cấu hình repo trong `bot/bot_config.json`
```json
{
  "org": "TEN_ORG_GITHUB",
  "repos": {
    "be": "TEN_REPO_BACKEND",
    "fe": "TEN_REPO_FRONTEND"
  },
  "monitored_repos": [
    "TEN_ORG/TEN_REPO_BACKEND",
    "TEN_ORG/TEN_REPO_FRONTEND"
  ],
  "poll_interval_seconds": 60,
  "webhook": { "port": 8765 }
}
```

---

## 🔄 Cơ Chế Review Hoạt Động

### Nguyên Tắc Nền Tảng

| Nguồn | Đóng Góp |
|:------|:---------|
| **Google Engineering Practices** | Tiêu chuẩn review: Approve nếu PR cải thiện code health. 10-point checklist. Quy tắc viết nhận xét lịch sự và có lý. |
| **PR-Agent Architecture** | Phân loại PR type, chấm điểm effort review (1-5 sao), slash commands `/review /improve /describe`, incremental re-review |
| **Antigravity AI (Ultra)** | Phân tích ngữ nghĩa sâu hơn rule-based: pattern recognition, domain-specific skills (Django, React, Security) |

### Mức Độ Nghiêm Trọng

| Mức | Ký Hiệu | Định Nghĩa | Hành Động |
|:----|:--------|:-----------|:----------|
| Critical | 🔴 | Bug crash, mất dữ liệu, lỗ hổng bảo mật | **Bắt buộc sửa** |
| Major | 🟡 | N+1 query, missing validation, logic sai | Nên sửa |
| Minor | 🟢 | Tối ưu nhỏ, naming | Nice-to-have |
| Suggestion | 💡 | Phương án thay thế tốt hơn | Optional |
| Nit | `Nit:` | Cú pháp, style, console.log | Non-blocking |

### Phán Quyết Tự Động

| Verdict | Điều Kiện |
|:--------|:----------|
| 🟢 **APPROVE** | Không có 🔴 Critical, ≤ 1 🟡 Major |
| 🟡 **COMMENT** | Không có 🔴, nhưng có ≥ 2 🟡 Major |
| 🔴 **REQUEST_CHANGES** | Có bất kỳ 🔴 Critical nào |

---

## 🗺️ Flow Toàn Bộ Công Cụ

```
┌─────────────────────────────────────────────────────────────────┐
│                      KÍCH HOẠT (3 cách)                         │
│  [ReviewBot.app]  [GitHub /review comment]  [Antigravity Chat]  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: THU THẬP DỮ LIỆU                                      │
│  gh pr view   → Metadata (title, author, branch, +/- lines)     │
│  gh pr diff   → Full diff của PR                                │
│  gh api reviews → Review cũ (dedup & re-review tracking)       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: PHÂN LOẠI & ĐỊNH TUYẾN                                 │
│  *.py / schema.py  → Backend Review (Django, N+1, Security)     │
│  *.jsx / *.tsx     → Frontend Review (React, CSS, Perf)         │
│  *.yml / Dockerfile → DevOps Review                             │
│  Lock files / Assets → SKIP                                     │
│                                                                 │
│  PR Type: Feature / Bug Fix / Performance / Refactor / Tests    │
│  Effort Score: ⭐1-5 (dựa vào số dòng và file thay đổi)        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: PHÂN TÍCH CODE                                         │
│  Rule-based:                                                    │
│  ├── N+1 Query (Django ORM không có select_related)             │
│  ├── CSS Sticky/Overflow conflict                               │
│  ├── Hardcoded credentials / secrets                            │
│  ├── GraphQL resolver thiếu null check                          │
│  └── console.log còn sót lại trong production code             │
│                                                                 │
│  Google 10-point Checklist:                                     │
│  Design / Functionality / Complexity / Tests / Naming /         │
│  Comments / Style / Documentation / Every Line / Context        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: GỬI LÊN GITHUB                                         │
│  ① General Review Comment (gh pr review)                        │
│    ├── 📊 Overview Dashboard (bảng đếm severity)               │
│    ├── 🔴/🟡/🟢 Danh sách findings + WHY + Fix suggestion      │
│    ├── 📋 Google Review Checklist (8 khía cạnh)                 │
│    └── 🟢/🟡/🔴 VERDICT                                        │
│                                                                 │
│  ② In-line Suggestions (GitHub Suggestion Blocks)               │
│    ├── Chỉ đích danh file:line cần sửa                          │
│    └── Author bấm "Commit suggestion" 1 click là xong          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 5: LƯU TRẠNG THÁI (state.json)                           │
│  Commit SHA → dùng cho Incremental Re-Review khi team sửa lỗi  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼ (Tùy chọn)
┌─────────────────────────────────────────────────────────────────┐
│  RE-REVIEW SAU KHI TEAM FIX                                     │
│  ✅ Resolved: Lỗi đã được sửa                                  │
│  ⚠️ Still Open: Lỗi chưa giải quyết                            │
│  🆕 New Issues: Lỗi mới phát sinh trong commit sửa             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Các Chế Độ Vận Hành

### Chế Độ 1: Interactive Dashboard (Khuyên dùng)
**Double-click** `ReviewBot.app` trên Desktop, hoặc:
```bash
python3 bot/bot.py --menu
```
→ Danh sách tất cả PR đang mở của cả BE + FE tự động hiển thị.
→ Gõ số để chọn PR → Chọn Review / Re-review / Mở browser.

### Chế Độ 2: Polling Daemon (Tự động quét ngầm)
```bash
python3 bot/bot.py --mode poll --interval 60
```
Bot chạy ngầm, tự review khi phát hiện commit mới.

### Chế Độ 3: Webhook + Cloudflare Tunnel (Tức thì)
```bash
python3 bot/bot.py --mode webhook --tunnel
```
→ Bot in ra URL `https://xxxx.trycloudflare.com/webhook`
→ Dán vào GitHub → Settings → Webhooks
→ Comment `/review` trên bất kỳ PR nào → Bot chạy ngay lập tức!

### Chế Độ 4: Antigravity IDE (AI sâu nhất)
```text
review pr 918 be
re-review pr 916 be
```

---

## 📁 Cấu Trúc Thư Mục

```
auto-review-pr-skill/
├── SKILL.md                   # Bộ não AI (prompt templates, routing rules)
├── README.md                  # Tài liệu này
├── bot/
│   ├── bot.py                 # Entry point chính, CLI & routing
│   ├── bot_config.json        # Cấu hình repo, port, features
│   ├── interactive_menu.py    # Giao diện dashboard tương tác
│   ├── review_engine.py       # Rule-based scanner + GitHub poster
│   ├── polling_daemon.py      # Polling loop (quét định kỳ)
│   ├── webhook_server.py      # HTTP server nhận GitHub events
│   ├── tunnel_manager.py      # Quản lý Cloudflare Tunnel
│   └── state.py               # Lưu commit SHA đã review (re-review)
├── scripts/
│   ├── review-pr.sh           # CLI wrapper shell script
│   └── routing.json           # File pattern → skill mapping
└── examples/
    └── USAGE.md               # Ví dụ sử dụng
```

---

## 🔐 Bảo Mật & Lưu Ý

- **Không commit `state.json`** — Đã có trong `.gitignore`
- **Token GitHub**: Dùng `gh auth login` riêng từng máy
- **Cloudflare URL thay đổi mỗi lần khởi động** — cần cập nhật Webhook URL trên GitHub mỗi lần bật lại bot
- **Port mặc định `8765`** — Tránh xung đột với Docker Desktop (port 8080)

---

## 🤝 Tham Khảo

- [Google Engineering Practices — Code Review](https://google.github.io/eng-practices/review/)
- [the-pr-agent/pr-agent](https://github.com/the-pr-agent/pr-agent)
- [Antigravity IDE](https://antigravity.dev/docs)
