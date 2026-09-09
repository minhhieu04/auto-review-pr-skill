# Auto-Review PR — Hướng Dẫn Sử Dụng

## Cách 1: Chạy trong Antigravity Chat (Đề xuất)

Chỉ cần nói:
```
review pr 916 be
```
hoặc:
```
review PR #1460 fe
```
hoặc review cả 2:
```
review pr 100 be fe
```

Agent sẽ tự động:
1. Fetch PR metadata + diff
2. Classify files → chọn skills phù hợp
3. Dispatch 2-3 subagent chuyên biệt song song
4. Tổng hợp findings
5. Post in-line suggestions lên GitHub
6. Báo cáo kết quả

## Cách 2: Chạy script prep (nếu muốn xem diff trước)

```bash
./scripts/review-pr.sh 916 be
./scripts/review-pr.sh 1460 fe
./scripts/review-pr.sh 100 be fe
```

Script sẽ:
- Fetch PR info + diff
- Classify files changed
- Check existing reviews
- Save diff vào `/tmp/` để agent đọc

## Review Output

Review sẽ được post lên GitHub dưới dạng:
1. **General review comment** — Tóm tắt tổng thể
2. **In-line suggestions** — Code suggestions trên từng dòng cụ thể

### Severity Levels
- 🔴 **Critical** — Must fix before merge (bugs, security, data loss)
- 🟡 **Major** — Should fix (performance, missing validation)
- 🟢 **Minor** — Nice to have (naming, style)
- 💡 **Suggestion** — Alternative approach

### Verdict Rules
- **APPROVE** — Không có Critical/Major issues
- **COMMENT** — Có Major nhưng không có Critical
- **REQUEST_CHANGES** — Có Critical issues

## Tùy Chỉnh

### Thay đổi routing rules
Edit `scripts/routing.json` để:
- Thêm/xóa file patterns
- Thay đổi skills mapping
- Điều chỉnh max suggestions

### Thay đổi review config
Trong `routing.json` > `review_config`:
- `max_inline_suggestions`: Giới hạn số inline comments (default: 10)
- `max_diff_lines`: Giới hạn diff size (default: 3000 lines)
- `auto_approve`: Tự động approve nếu pass (default: false)
