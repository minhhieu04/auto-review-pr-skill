# 🤖 PR-Agent & Antigravity Auto-Review System

Hệ thống tự động review mã nguồn Pull Request kết hợp tiêu chuẩn **[Google Engineering Practices](https://google.github.io/eng-practices/review/)** và các tính năng mạnh mẽ của **[the-pr-agent/pr-agent](https://github.com/the-pr-agent/pr-agent)**.

---

## 🌟 Tính Năng Nổi Bật

1. **Chuẩn mực Google Engineering Practices**:
   - Tiêu chuẩn: Ưu tiên duyệt PR nếu nó cải thiện sức khỏe tổng thể của codebase.
   - Bảng kiểm tra 10 khía cạnh: Thiết kế, Tính năng, Độ phức tạp, Kiểm thử, Đặt tên, Chú thích, Phong cách, Tài liệu, Đọc từng dòng, Ngữ cảnh xung quanh.
   - Văn hóa nhận xét: Nhận xét lịch sự, giải thích rõ nguyên do (**WHY**), hướng vào **code** thay vì lập trình viên, gắn nhãn `Nit:` cho các góp ý nhỏ.
2. **Cơ chế PR-Agent**:
   - Phân loại PR: Feature, Bug Fix, Refactor, Performance, Tests, Docs.
   - Chấm điểm nỗ lực review (Effort 1-5 sao).
   - Hỗ trợ các lệnh: `/review`, `/improve`, `/describe`, `/ask`.
3. **Bảng Tổng Quan (Overview Dashboard)**:
   - Thống kê chi tiết số lỗi theo mức độ: 🔴 Critical, 🟡 Major, 🟢 Minor, 💡 Suggestions, Nit.
   - Phán quyết rõ ràng: `APPROVE`, `COMMENT`, hoặc `REQUEST_CHANGES`.
4. **Gợi ý Code trực tiếp (In-line GitHub Suggestions)**:
   - Chỉ đích danh dòng code cần sửa kèm block `suggestion` để tác giả có thể bấm commit ngay trên web.
5. **Đánh giá tăng dần (Incremental Re-Review)**:
   - Khi tác giả commit sửa lỗi, bot tự động so sánh diff mới và đánh dấu những lỗi đã được khắc phục (Resolved).

---

## 🚀 3 Cách Vận Hành Bot

### Cách 1: Chạy trực tiếp trong Antigravity IDE
Mở khung chat của Antigravity và gõ:
```text
review pr 916 be
```
hoặc khi có commit mới:
```text
re-review pr 916 be
```

### Cách 2: Chạy Polling Daemon (Thăm dò ngầm định kỳ)
Bot sẽ tự động quét danh sách PR đang mở mỗi 60 giây. Nếu phát hiện commit mới, bot sẽ tự động thực hiện review:
```bash
python3 bot/bot.py --mode poll --interval 60
```

### Cách 3: Chạy Webhook Server qua Cloudflare Tunnel (Miễn phí 100%)
Nhận sự kiện tức thì từ GitHub khi có PR mở hoặc khi ai đó comment `/review`:

1. Cài đặt `cloudflared` (nếu chưa có):
   ```bash
   brew install cloudflared
   ```
2. Khởi động Webhook kèm Cloudflare Tunnel:
   ```bash
   python3 bot/bot.py --mode webhook --tunnel
   ```
3. Copy URL Public dạng `https://xxxx.trycloudflare.com/webhook` được in ra trên màn hình và dán vào:
   - **GitHub Repo -> Settings -> Webhooks -> Add webhook**
   - **Payload URL**: `https://xxxx.trycloudflare.com/webhook`
   - **Content type**: `application/json`
   - **Events**: Chọn *Pull requests* và *Issue comments*.

### Chạy thủ công 1 PR bất kỳ qua CLI:
```bash
python3 bot/bot.py --pr 916 --repo be
python3 bot/bot.py --pr 1460 --repo fe
```

---

## ⚙️ Cấu Hình (`bot/bot_config.json`)

```json
{
  "org": "deveop-com",
  "monitored_repos": [
    "deveop-com/clickessms_be",
    "deveop-com/clickessms_fe"
  ],
  "poll_interval_seconds": 60,
  "webhook": {
    "port": 8080
  },
  "features": {
    "auto_review_on_pr_opened": true,
    "auto_review_on_commit_push": true,
    "pr_agent_slash_commands": true,
    "google_practices_checklist": true,
    "overview_dashboard": true,
    "incremental_re_review": true
  }
}
```
