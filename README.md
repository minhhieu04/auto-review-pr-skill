# 🤖 Universal PR-Agent & Antigravity Auto-Review System

> **Hệ thống tự động review Pull Request độc lập, đa tài khoản, đa kiến trúc Subagents cho MỌI dự án GitHub.**  
> Kết hợp tiêu chuẩn **[Google Engineering Practices](https://google.github.io/eng-practices/review/)** + kiến trúc **[PR-Agent](https://github.com/the-pr-agent/pr-agent)** + **Antigravity AI** (Google Ultra).

---

## 🌟 Tính Năng Đột Phá — Độc Lập & Scale Toàn Diện

1. **Chế Độ Review Kép Thông Minh (Dual-Mode: AI LLM + Local Subagents)**:
   - **Chế độ AI Siêu Tốc (AI Mode)**: Tích hợp trực tiếp Google Gemini (`gemini-3.8-flash`, `gemini-3.6-flash`), DeepSeek (`deepseek-reasoner`), hoặc OpenAI (`gpt-5`). Đọc toàn bộ 5 gói rules và git diff, phân tích toàn diện trong vài giây.
   - **Tự Động Fallback Không Treo**: Nếu quota API cạn hoặc server bận (429/503), bot tự động chuyển model dự phòng hoặc rơi về **Local Subagents** an toàn tuyệt đối mà không bị gián đoạn.
   - **Bảo Mật & Lưu Trữ API Key Tự Động**: Key được lưu trong file `bot/.env` (được `.gitignore` bảo vệ), tự động load lại khi mở bot, che giấu ký tự trên giao diện (`AQ.Ab8...C0dg`).

2. **Inline Code Suggestions 1-Click Trực Tiếp Trên GitHub**:
   - Không chỉ nhận xét chung chung, hệ thống **ghim thẳng comment vào từng dòng code bị lỗi** trên tab *Files changed* của PR.
   - Kèm khối mã đề xuất chuẩn GitHub (````suggestion ... ````) — lập trình viên chỉ cần bấm nút **"Commit suggestion"** (1 click) trực tiếp trên GitHub để sửa code ngay!
   - Tự động map và căn chỉnh số dòng (Diff Alignment) với các dòng thay đổi thực tế trong PR để đảm bảo không bị lỗi diff.

3. **Kiến Trúc Multi-Subagents Song Song (Parallel Specialized Agents)**:
   - Khi không dùng API Key, hệ thống tự kích hoạt **4 Subagents chuyên môn hóa chạy song song**:
     - ⚙️ **Backend Reviewer Subagent**: ORM, N+1 queries, SQL Injection, API boundaries, migrations.
     - 🎨 **Frontend Performance Subagent**: React hooks, re-renders, layout CSS sticky/overflow, TypeScript, A11y.
     - 🛡️ **Security Auditor Subagent**: Rà soát secrets, API keys, AWS keys, Private keys, TLS/SSL verify.
     - 🧪 **Resilience & QA Subagent**: Anti-patterns trong test, sleep delays, Docker unpinned tags, edge-cases.
   - Các subagents chạy đồng thời và gắn thẻ `[Agent Name]` vào từng issue tìm thấy trên GitHub!

4. **Quản Lý Nhiều Tài Khoản Git (Multi-Account Switcher & Repo Browser)**:
   - Tự động nhận diện nếu máy có **nhiều tài khoản GitHub** (cá nhân, công ty...).
   - **`[u] Chuyển Git User`**: Chuyển tài khoản active tức thì qua `gh auth switch`.
   - **`[s] Chọn từ Repos của tôi`**: Tự động tải danh sách toàn bộ repos của user đó để chọn review ngay với 1 phím bấm!

5. **100% Độc Lập (Self-Contained Knowledge Base)**:
   - Toàn bộ tri thức review (5 gói `rules/`) được nhúng trực tiếp trong repo.
   - Người khác clone về máy là dùng được ngay, **không cần cài thêm bất kỳ skill ngoài nào**.

6. **Dùng Cho Mọi Dự Án (Project-Agnostic & Auto-Detect)**:
   - **Tự động nhận diện Git repo**: Mở terminal ở bất kỳ thư mục dự án nào, bot tự động nhận diện `owner/repo`.
   - **Thêm repo tùy ý qua Menu `[a]`**: Nhập hoặc paste link bất kỳ GitHub repo nào.

---

## ⚙️ Yêu Cầu Tối Thiểu

| Mục | Yêu Cầu |
|:----|:---------|
| **Hệ điều hành** | macOS 12+, Linux Ubuntu 20+, Windows 10+ (WSL) |
| **Python** | 3.9+ (trên Mac M-series: `/opt/homebrew/bin/python3`) |
| **GitHub CLI** | `gh` 2.0+ — đã chạy `gh auth login` với quyền `repo` |
| **Antigravity IDE** | Bản mới nhất (dùng Google Ultra quota để review AI thông minh nhất) |
| **cloudflared** | Tùy chọn — chỉ cần nếu bật Webhook + Cloudflare Tunnel |

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
# Chọn: GitHub.com -> SSH/HTTPS -> Đăng nhập (có thể add nhiều tài khoản)
```

---

## 📚 Bộ Tri Thức Đóng Gói Sẵn (`rules/`)

Hệ thống được nhúng sẵn 5 gói quy tắc chuyên sâu, không cần cài thêm bất kỳ skill nào khác:

| Gói Quy Tắc | File | Nội Dung Trọng Tâm |
|:------------|:-----|:-------------------|
| **Google Standards** | `rules/01_google_engineering_practices.md` | 10 tiêu chí đánh giá Google, quy tắc viết nhận xét lịch sự, logic phán quyết APPROVE / COMMENT / REQUEST_CHANGES. |
| **Backend & ORM** | `rules/02_backend_architecture.md` | N+1 queries, Django/TypeORM/Prisma/SQLAlchemy, migration table locks, API validation, transaction boundaries. |
| **Frontend & UI/UX** | `rules/03_frontend_architecture.md` | React hooks rules, dependency array, unnecessary re-renders, sticky + overflow bug, WCAG 2.1 AA accessibility. |
| **Security & Defense** | `rules/04_security_and_defense.md` | Phát hiện lộ API Keys/Tokens/Private Keys, SQL Injection, XSS, Defense-in-depth 3 tầng. |
| **Testing & Resilience** | `rules/05_testing_and_resilience.md` | Anti-patterns (không test mock), loại bỏ sleep/setTimeout hardcoded, race conditions, timeout handling. |

---

## 🚀 Các Chế Độ Vận Hành

### Chế Độ 1: Universal Dashboard (Khuyên Dùng)
Double-click `ReviewBot.app` trên Desktop, hoặc chạy:
```bash
python3 bot/bot.py --menu
```

**Giao diện trực quan:**
```
======================================================================
    ANTIGRAVITY & PR-AGENT — UNIVERSAL CODE REVIEW DASHBOARD
======================================================================
  Git User: @minhhieu04 (Active) | Current Dir: deveop-com/clickessms_be
  Loading open PRs...

  📦 DEVEOP-COM/CLICKESSMS_BE [current dir]
  ──────────────────────────────────────────────────────────────────
  [ 1] #919  fix(PW2-1006): update password reset...  @minhhieu04 [mine]
  [ 2] #918  feat(PW2-977): warning to calculation   @nguyennhatninh

  OTHER OPTIONS:
  [s]  Chọn từ Repos của tôi (Browse & Select My GitHub Repos)
  [u]  Chuyển Git User (Switch Active GitHub Account)
  [a]  Thêm / Chuyển Repo khác (Add any GitHub repo to monitor)
  [k]  Cấu hình AI Provider / API Key (Gemini, DeepSeek, OpenAI)
  [c]  Custom PR number (nhập số PR & repo thủ công)
  [m]  Review NHIỀU PR cùng lúc (vd: 1 3 5)
  [w]  Webhook + Cloudflare Tunnel (tức thì từ GitHub)
  [p]  Polling Daemon (tự động quét ngầm)
  [r]  Refresh danh sách PR
  [q]  Thoát
======================================================================
```

**Tính Năng Tiện Lợi:**
- **`[k] Cấu hình AI Provider`**: Đổi giữa Google Gemini (`gemini-3.8-flash`), DeepSeek, OpenAI (`gpt-5`), test kết nối tức thì, tự động lưu API Key vào `.env` bảo mật.
- **`[s] Repos của tôi`**: Xem toàn bộ repositories của tài khoản hiện tại, bấm số để chọn ngay.
- **`[u] Đổi Git User`**: Chuyển đổi giữa các tài khoản GitHub đã đăng nhập trên máy chỉ bằng 1 thao tác.
- **`[m] Review nhiều PR`**: Gõ `1 3 5` → Bot tự động điều phối review tuần tự từng PR.
- **Tự sửa khi gõ sai**: Nhập sai ký tự → nhắc nhập lại tại chỗ, không reload lại toàn bộ menu.

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
AI sẽ tự động dispatch các subagent tương ứng và áp dụng các gói `rules/*.md` để phân tích sâu từng dòng code và đề xuất code suggestion chuẩn chỉ.

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
│   ├── llm_client.py         # Client gọi AI (Gemini/DeepSeek/OpenAI, fallback, quota check)
│   ├── .env                  # Lưu API Keys bảo mật (được gitignore)
│   ├── interactive_menu.py   # Dashboard tương tác, multi-user, repo browser, AI settings
│   ├── review_engine.py      # Bộ điều phối Dual-Mode (AI + 4 Subagents song song)
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
