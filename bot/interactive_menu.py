import os
import sys
import json
import subprocess
from typing import List, Dict, Any, Optional

# ANSI Color codes
BOLD = "\033[1m"
GREEN = "\033[0;32m"
BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
DIM = "\033[2m"
RESET = "\033[0m"

def clear_screen():
    os.system("clear" if os.name != "nt" else "cls")

def fetch_open_prs(repo: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Fetch open PRs using gh CLI."""
    try:
        res = subprocess.run([
            "gh", "pr", "list",
            "--repo", repo,
            "--state", "open",
            "--limit", str(limit),
            "--json", "number,title,author,headRefName,updatedAt"
        ], capture_output=True, text=True, check=True)
        return json.loads(res.stdout)
    except Exception as e:
        print(f"{YELLOW}⚠️ Không thể lấy danh sách PR từ {repo}: {e}{RESET}")
        return []

def open_pr_in_browser(repo: str, pr_number: int):
    try:
        subprocess.run(["gh", "pr", "view", str(pr_number), "--repo", repo, "--web"], check=True)
    except Exception as e:
        print(f"{RED}Không thể mở trình duyệt: {e}{RESET}")

def run_interactive_menu(engine, state_manager, config: Dict[str, Any]):
    repos = config.get("monitored_repos", ["deveop-com/clickessms_be", "deveop-com/clickessms_fe"])
    org = config.get("org", "deveop-com")
    repos_map = config.get("repos", {"be": "clickessms_be", "fe": "clickessms_fe"})

    while True:
        clear_screen()
        print(f"{BLUE}======================================================================{RESET}")
        print(f"{GREEN}{BOLD}    🤖 ANTIGRAVITY & PR-AGENT — INTERACTIVE REVIEW DASHBOARD{RESET}")
        print(f"{BLUE}======================================================================{RESET}")
        print(f"{DIM}Đang tải danh sách PR mới nhất từ GitHub...{RESET}")

        pr_options = []
        option_index = 1

        for repo in repos:
            repo_short = repo.split("/")[-1]
            icon = "📦" if "be" in repo_short else "🎨"
            print(f"\n{BOLD}{icon} {repo_short.upper()}{RESET} ({repo})")

            prs = fetch_open_prs(repo, limit=5)
            if not prs:
                print(f"  {DIM}(Không có PR nào đang mở){RESET}")
                continue

            for pr in prs:
                author = pr.get("author", {}).get("login", "unknown")
                title = pr.get("title", "")
                if len(title) > 55:
                    title = title[:52] + "..."
                
                print(f"  {YELLOW}[{option_index}]{RESET} #{pr['number']:<5} {CYAN}{title:<56}{RESET} {DIM}@{author}{RESET}")
                pr_options.append({
                    "index": option_index,
                    "repo": repo,
                    "number": pr["number"],
                    "title": pr["title"],
                    "author": author
                })
                option_index += 1

        print(f"\n{BLUE}----------------------------------------------------------------------{RESET}")
        print(f"{BOLD}⚡ TÙY CHỌN KHÁC:{RESET}")
        print(f"  {YELLOW}[c]{RESET} Nhập số PR bất kỳ bằng tay (Custom PR number)")
        print(f"  {YELLOW}[w]{RESET} Bật Webhook Server + Cloudflare Tunnel (Lắng nghe sự kiện từ GitHub)")
        print(f"  {YELLOW}[p]{RESET} Bật Polling Daemon (Tự động quét PR mỗi 60s)")
        print(f"  {YELLOW}[r]{RESET} Làm mới danh sách PR (Refresh)")
        print(f"  {YELLOW}[q]{RESET} Thoát")
        print(f"{BLUE}======================================================================{RESET}")

        choice = input(f"\n👉 {BOLD}Nhập lựa chọn của bạn:{RESET} ").strip().lower()

        if choice == "q":
            print(f"\n{GREEN}Tạm biệt anh Hiếu! Chúc anh một ngày làm việc hiệu quả.{RESET}\n")
            sys.exit(0)

        elif choice == "r" or choice == "":
            continue

        elif choice == "w":
            from tunnel_manager import CloudflareTunnel
            from webhook_server import start_webhook_server
            port = config.get("webhook", {}).get("port", 8765)
            tunnel = CloudflareTunnel(port=port)
            tunnel.start()
            try:
                start_webhook_server(port=port, engine=engine, commands=config.get("supported_commands", []))
            except KeyboardInterrupt:
                tunnel.stop()
                print("\n⏹️ Đã dừng Webhook.")
                input("\nBấm Enter để quay lại menu...")

        elif choice == "p":
            from polling_daemon import PollingDaemon
            interval = config.get("poll_interval_seconds", 60)
            daemon = PollingDaemon(repos=repos, engine=engine, state_manager=state_manager, interval=interval)
            try:
                daemon.start()
            except KeyboardInterrupt:
                print("\n⏹️ Đã dừng Polling Daemon.")
                input("\nBấm Enter để quay lại menu...")

        elif choice == "c":
            print(f"\n{BOLD}📝 Nhập thông tin PR:{RESET}")
            pr_input = input("  Nhập số PR (vd: 916): ").strip()
            if not pr_input.isdigit():
                print(f"{RED}Số PR không hợp lệ!{RESET}")
                input("Bấm Enter để tiếp tục...")
                continue
            
            repo_type = input("  Chọn repo (be / fe, mặc định: be): ").strip().lower()
            if repo_type in repos_map:
                target_repo = f"{org}/{repos_map[repo_type]}"
            elif "/" in repo_type:
                target_repo = repo_type
            else:
                target_repo = f"{org}/{repos_map.get('be', 'clickessms_be')}"

            selected_pr = {
                "repo": target_repo,
                "number": int(pr_input),
                "title": f"PR #{pr_input}",
                "author": "manual"
            }
            _handle_pr_actions(engine, selected_pr)

        elif choice.isdigit():
            idx = int(choice)
            matched = next((p for p in pr_options if p["index"] == idx), None)
            if not matched:
                print(f"{RED}Lựa chọn không hợp lệ!{RESET}")
                input("Bấm Enter để tiếp tục...")
                continue
            _handle_pr_actions(engine, matched)

        else:
            print(f"{RED}Lựa chọn không hợp lệ!{RESET}")
            input("Bấm Enter để tiếp tục...")

def _handle_pr_actions(engine, pr_info: Dict[str, Any]):
    repo = pr_info["repo"]
    number = pr_info["number"]
    title = pr_info["title"]

    while True:
        clear_screen()
        repo_short = repo.split("/")[-1]
        print(f"{BLUE}======================================================================{RESET}")
        print(f"{GREEN}{BOLD}    🎯 ĐANG CHỌN: [{repo_short.upper()} #{number}]{RESET}")
        print(f"    Tiêu đề: {CYAN}{title}{RESET}")
        print(f"{BLUE}======================================================================{RESET}")
        print(f"\n{BOLD}Chọn thao tác thực hiện:{RESET}")
        print(f"  {YELLOW}[1]{RESET} 🚀 {BOLD}Review toàn diện{RESET} (Google Standards + Overview Dashboard + In-line Suggestions) {GREEN}[Mặc định]{RESET}")
        print(f"  {YELLOW}[2]{RESET} 🔄 {BOLD}Re-review{RESET} (Kiểm tra commit mới nhất kể từ lần review trước)")
        print(f"  {YELLOW}[3]{RESET} 🌐 {BOLD}Mở PR trên trình duyệt{RESET} (GitHub Web)")
        print(f"  {YELLOW}[b]{RESET} ⬅️  Quay lại danh sách PR")
        print(f"{BLUE}======================================================================{RESET}")

        sub_choice = input(f"\n👉 {BOLD}Nhập lựa chọn [1-3 / b] (Mặc định: 1):{RESET} ").strip().lower()
        if sub_choice == "" or sub_choice == "1":
            print(f"\n{GREEN}🚀 Đang tiến hành review {repo} PR #{number}...{RESET}\n")
            try:
                res = engine.execute_review(repo, number)
                print(f"\n{GREEN}✅ Hoàn thành review! Đã gửi đánh giá và gợi ý code lên GitHub.{RESET}\n")
            except Exception as e:
                print(f"\n{RED}❌ Có lỗi xảy ra trong quá trình review: {e}{RESET}\n")

            ask_web = input("🌐 Bạn có muốn mở PR trên trình duyệt để xem kết quả? (y/N): ").strip().lower()
            if ask_web == "y":
                open_pr_in_browser(repo, number)

            input("\nBấm Enter để quay lại menu chính...")
            break

        elif sub_choice == "2":
            print(f"\n{GREEN}🔄 Đang kiểm tra thay đổi commit mới cho {repo} PR #{number}...{RESET}\n")
            try:
                res = engine.execute_review(repo, number)
                print(f"\n{GREEN}✅ Hoàn tất Re-review!{RESET}\n")
            except Exception as e:
                print(f"\n{RED}❌ Có lỗi xảy ra: {e}{RESET}\n")

            ask_web = input("🌐 Bạn có muốn mở PR trên trình duyệt? (y/N): ").strip().lower()
            if ask_web == "y":
                open_pr_in_browser(repo, number)

            input("\nBấm Enter để quay lại menu chính...")
            break

        elif sub_choice == "3":
            print(f"\n{BLUE}Đang mở PR #{number} trên trình duyệt...{RESET}")
            open_pr_in_browser(repo, number)
            input("\nBấm Enter để tiếp tục...")

        elif sub_choice == "b":
            break
