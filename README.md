# 🤖 Universal PR-Agent & Antigravity Auto-Review System

> **Hệ thống tự động review Pull Request độc lập và mở rộng cho MỌI dự án GitHub.**  
> Kết hợp tiêu chuẩn **[Google Engineering Practices](https://google.github.io/eng-practices/review/)** + kiến trúc **[PR-Agent](https://github.com/the-pr-agent/pr-agent)** + **Antigravity AI** (Google Ultra).

---

## 🌟 Tính Năng Đột Phá — Độc Lập & Scale Toàn Diện

1. **100% Độc Lập (Self-Contained Knowledge Base)**:
   - Không phụ thuộc vào bất kỳ skill cài ngoài nào trên máy cá nhân!
   - Toàn bộ tri thức review (Backend, Frontend, Security, Testing, Google Standards) được đóng gói sẵn trong thư mục `rules/` của repository này.
   - Bất kỳ ai clone về máy (dù chưa từng cài skill nào) đều có 100% sức mạnh review chuẩn tech lead.

2. **Dùng Cho Mọi Dự Án (Project-Agnostic & Auto-Detect)**:
   - **Tự động nhận diện Git repo**: Nếu mở terminal trong bất kỳ thư mục dự án nào, bot tự động nhận diện `owner/repo` qua git remote và ưu tiên hiển thị.
   - **Thêm repo tùy ý qua Menu**: Bấm `[a]` để gõ hoặc dán link bất kỳ GitHub repo nào (`facebook/react`, `owner/my-service`, etc.).
   - Hỗ trợ đa ngôn ngữ: Python (Django, FastAPI), TypeScript/JavaScript (React, Next.js, Node/Nest), Go, Java, Docker, SQL...

---

## ⚙️ Yêu Cầu Tối Thiểu

| Mục | Yêu Cầu |
|:----|:---------|
| **Hệ điều hành** | macOS 12+, Linux Ubuntu 20+, Windows 10+ (WSL) |
| **Python** | 3.9+ (trên Mac M-series: `/opt/homebrew/bin/python3`) |
| **GitHub CLI** | `gh` 2.0+ — đã chạy `gh auth login` với quyền `repo` |
| **Antigravity IDE** | Bản mới nhất (dùng Google Ultra quota để review AI thông minh nhất) |
| **cloudflared** | Tùy chọn — chỉ cần nếu bật Webhook + Cloudflare Tunnel |

> **Máy người khác dùng được ngay:**  
> Bot tự động nhận diện user qua `gh api user` và tự động lấy repo hiện tại. Đồng nghiệp chỉ cần `gh auth login` tài khoản của họ là chạy được ngay!

---

## 🛠️ Cài Đặt

### 1. Clone repository
```bash
git clone git@github.com:minhhieu04/auto-review-pr-skill.git
cd auto-review-pr-skill
```

### 2. Cài GitHub CLI & đăng nhập (1 lần duy nhất)
```bash
# macOS
brew install gh
gh auth login
# Chọn: GitHub.com -> SSH/HTTPS -> Đăng nhập
```

### 3. Cấu hình danh sách repo theo dõi (`bot/bot_config.json`)
Bạn có thể cấu hình trước các repo thường dùng, hoặc thêm trực tiếp trên giao diện:
```json
{
  "monitored_repos": [
    "owner/repo-backend",
    "owner/repo-frontend"
  ],
  "poll_interval_seconds": 60,
  "webhook": { "port": 8765 }
}
```

---

## 📚 Bộ Tri Thức Đóng Gói Sẵn (`rules/`)

Hệ thống được nhúng sẵn 5 gói quy tắc chuyên sâu, không cần cài thêm bất kỳ skill nào khác:

| Gói Quy Tắc | File | Nội Dung Trọng Tâm |
|:------------|:-----|:-------------------|
| **Google Standards** | `rules/01_google_engineering_practices.md` | 10 tiêu chí đánh giá Google, quy tắc viết nhận xét lịch sự, logic phán quyết APPROVE / COMMENT / REQUEST_CHANGES. |
| **Backend & ORM** | `rules/02_backend_architecture.md` | N+1 queries, Django/TypeORM/Prisma, migration table locks, API validation, transaction boundaries. |
| **Frontend & UI/UX** | `rules/03_frontend_architecture.md` | React hooks rules, dependency array, unnecessary re-renders, sticky + overflow bug, WCAG 2.1 AA accessibility. |
| **Security & Defense** | `rules/04_security_and_defense.md` | Phát hiện lộ API Keys/Tokens/Private Keys, SQL Injection, XSS, Defense-in-depth 3 tầng. |
| **Testing & Resilience** | `rules/05_testing_and_resilience.md` | Anti-patterns (không test mock), cấm sleep/setTimeout hardcoded, race conditions, timeout handling. |

---

## 🚀 Các Chế Độ Vận Hành

### Chế Độ 1: Interactive Dashboard (Khuyên Dùng)
Double-click `ReviewBot.app` trên Desktop, hoặc chạy:
```bash
python3 bot/bot.py --menu
```

**Giao diện trực quan:**
```
======================================================================
    ANTIGRAVITY & PR-AGENT — UNIVERSAL CODE REVIEW DASHBOARD
======================================================================
  User: @minhhieu04 | Current Dir Repo: deveop-com/clickessms_be
  Loading open PRs...

  📦 DEVEOP-COM/CLICKESSMS_BE [current dir]
  ──────────────────────────────────────────────────────────────────
  [ 1] #919  fix(PW2-1006): update password reset...  @minhhieu04 [mine]
  [ 2] #918  feat(PW2-977): warning to calculation   @nguyennhatninh

  OTHER OPTIONS:
  [a]  Thêm / Chuyển Repo khác (Add any GitHub repo to monitor)
  [c]  Custom PR number (nhập số PR & repo thủ công)
  [m]  Review NHIỀU PR cùng lúc (vd: 1 3 5)
  [w]  Webhook + Cloudflare Tunnel (tức thì từ GitHub)
  [p]  Polling Daemon (tự động quét ngầm)
  [r]  Refresh danh sách PR
  [q]  Thoát
======================================================================
```

**Tính Năng Tiện Lợi:**
- **Thêm Repo tùy ý `[a]`**: Nhập bất kỳ repo GitHub nào để nạp danh sách PR ngay.
- **Review hàng loạt `[m]`**: Gõ `1 3 5` → Bot tự động review lần lượt và in bảng tổng kết.
- **Tự sửa khi nhập sai**: Nhập sai ký tự → hệ thống nhắc nhập lại ngay tại chỗ, không reload lại toàn bộ menu.

---

### Chế Độ 2: Polling Daemon (Tự Động Quét Ngầm)
Bấm `[p]` từ menu hoặc chạy:
```bash
python3 bot/bot.py --mode poll --interval 60
```
Có 3 tùy chọn lọc:
1. `[1]` Quét toàn bộ PR đang mở.
2. `[2]` Chỉ quét PR cần bạn review (`reviewer = @me`).
3. `[3]` Chỉ quét PR được giao cho bạn (`assignee = @me`).
> **Dừng quét**: Nhấn `Ctrl+C` bất kỳ lúc nào để dừng an toàn và trở về menu.

---

### Chế Độ 3: Webhook + Cloudflare Tunnel (Tức Thì Từ GitHub)
```bash
python3 bot/bot.py --mode webhook --tunnel
```
Bot tự động tạo URL public dạng `https://xxxx.trycloudflare.com/webhook`.  
Thêm webhook này vào GitHub repo của bạn → Mỗi khi ai đó comment `/review` trên PR, bot sẽ tự động review ngay lập tức!

---

### Chế Độ 4: Antigravity IDE (AI Phân Tích Sâu Nhất)
Trong chat của Antigravity IDE:
```text
review pr 918
review pr 123 in facebook/react
re-review pr 916
```
AI sẽ tự động đọc `SKILL.md` và các gói `rules/*.md` để phân tích sâu từng dòng code và đề xuất code suggestion chuẩn chỉ.

---

## 📁 Cấu Trúc Repository

```
auto-review-pr-skill/
├── SKILL.md                  # Brain chỉ dẫn cho AI Agent (Universal)
├── README.md                 # Hướng dẫn chi tiết
├── rules/                    # 📚 Bộ tri thức review đóng gói sẵn
│   ├── 01_google_engineering_practices.md
│   ├── 02_backend_architecture.md
│   ├── 03_frontend_architecture.md
│   ├── 04_security_and_defense.md
│   └── 05_testing_and_resilience.md
├── bot/
│   ├── bot.py                # Entrypoint CLI & routing thông minh
│   ├── bot_config.json       # File cấu hình repo & port
│   ├── interactive_menu.py   # Dashboard tương tác, auto-detect git
│   ├── review_engine.py      # Bộ quét lỗi đa ngôn ngữ (Python, JS/TS, Security)
│   ├── polling_daemon.py     # Quét định kỳ (All / Reviewer / Assignee)
│   ├── webhook_server.py     # HTTP Server nhận Webhook GitHub
│   ├── tunnel_manager.py     # Quản lý Cloudflare Tunnel
│   └── state.py              # Lưu commit SHA (hỗ trợ Re-review)
└── scripts/
    ├── review-pr.sh          # Script chạy nhanh từ terminal
    └── routing.json          # File pattern routing
```

---

## 🔐 Bảo Mật & Lưu Ý

- Không hardcode token vào code. Toàn bộ xác thực qua `gh auth login`.
- File `state.json` được tự động bỏ qua qua `.gitignore`.
- Port mặc định của bot là `8765` (tránh xung đột với Docker cổng 8080).

---

## 🤝 Tham Khảo

- [Google Engineering Practices — Code Review](https://google.github.io/eng-practices/review/)
- [the-pr-agent/pr-agent](https://github.com/the-pr-agent/pr-agent)
