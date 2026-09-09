import os
import sys
import json
import re
import subprocess
import threading
from typing import List, Dict, Any, Optional

# ANSI Color codes
BOLD = "\033[1m"
GREEN = "\033[0;32m"
BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
DIM = "\033[2m"
MAGENTA = "\033[0;35m"
RESET = "\033[0m"

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_config.json")

def clear_screen():
    os.system("clear" if os.name != "nt" else "cls")

def detect_current_repo() -> Optional[str]:
    """Auto-detect GitHub repo (owner/repo) from current directory's git remote."""
    try:
        url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
        m = re.search(r"github\.com[:/]([\w\-]+)/([\w\-]+?)(?:\.git)?$", url)
        if m:
            return f"{m.group(1)}/{m.group(2)}"
    except Exception:
        pass
    return None

def fetch_open_prs(repo: str, limit: int = 8, assigned_to: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch open PRs using gh CLI. Optionally filter by assignee."""
    cmd = [
        "gh", "pr", "list",
        "--repo", repo,
        "--state", "open",
        "--limit", str(limit),
        "--json", "number,title,author,assignees,headRefName,updatedAt"
    ]
    if assigned_to:
        cmd += ["--assignee", assigned_to]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(res.stdout)
    except Exception as e:
        print(f"{YELLOW}⚠️  Cannot fetch PRs from {repo}: {e}{RESET}")
        return []

def fetch_current_gh_user() -> str:
    try:
        res = subprocess.run(["gh", "api", "user", "--jq", ".login"],
                             capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return ""

def open_pr_in_browser(repo: str, pr_number: int):
    try:
        subprocess.run(["gh", "pr", "view", str(pr_number), "--repo", repo, "--web"], check=True)
    except Exception as e:
        print(f"{RED}Cannot open browser: {e}{RESET}")

def save_monitored_repos(config: Dict[str, Any], repos: List[str]):
    config["monitored_repos"] = repos
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"{YELLOW}Could not save config: {e}{RESET}")

def run_interactive_menu(engine, state_manager, config: Dict[str, Any]):
    repos = list(config.get("monitored_repos", []))
    org = config.get("org", "deveop-com")
    repos_map = config.get("repos", {"be": "clickessms_be", "fe": "clickessms_fe"})
    current_user = fetch_current_gh_user()

    # Auto-detect repo if running inside a git directory
    detected_repo = detect_current_repo()
    if detected_repo and detected_repo not in repos:
        repos.insert(0, detected_repo)

    if not repos:
        repos = ["deveop-com/clickessms_be", "deveop-com/clickessms_fe"]

    while True:
        clear_screen()
        print(f"{BLUE}======================================================================{RESET}")
        print(f"{GREEN}{BOLD}    ANTIGRAVITY & PR-AGENT — UNIVERSAL CODE REVIEW DASHBOARD{RESET}")
        print(f"{BLUE}======================================================================{RESET}")
        header_info = []
        if current_user:
            header_info.append(f"User: {CYAN}@{current_user}{RESET}")
        if detected_repo:
            header_info.append(f"Current Dir Repo: {GREEN}{detected_repo}{RESET}")
        if header_info:
            print(f"  {DIM}{' | '.join(header_info)}{RESET}")
            print(f"  {DIM}Loading open PRs...{RESET}")

        pr_options: List[Dict[str, Any]] = []
        option_index = 1

        for repo in repos:
            repo_short = repo.split("/")[-1]
            is_curr = f" {GREEN}[current dir]{RESET}" if repo == detected_repo else ""
            print(f"\n  {BOLD}📦 {repo.upper()}{RESET}{is_curr}")
            print(f"  {'─' * 66}")

            prs = fetch_open_prs(repo, limit=8)
            if not prs:
                print(f"  {DIM}(No open PRs in {repo}){RESET}")
                continue

            for pr in prs:
                author = pr.get("author", {}).get("login", "?")
                title = pr.get("title", "")
                title_display = title[:53] + "..." if len(title) > 56 else title
                assignees = [a.get("login", "") for a in pr.get("assignees", [])]
                mine_tag = f" {GREEN}[mine]{RESET}" if current_user and current_user in assignees else ""

                print(f"  {YELLOW}[{option_index:>2}]{RESET} #{pr['number']:<5} {CYAN}{title_display:<56}{RESET} {DIM}@{author}{RESET}{mine_tag}")
                pr_options.append({
                    "index": option_index,
                    "repo": repo,
                    "number": pr["number"],
                    "title": pr["title"],
                    "author": author
                })
                option_index += 1

        print(f"\n{BLUE}  {'─' * 66}{RESET}")
        print(f"{BOLD}  OTHER OPTIONS:{RESET}")
        print(f"  {YELLOW}[a]{RESET}  Thêm / Chuyển Repo khác {DIM}(Add any GitHub repo to monitor){RESET}")
        print(f"  {YELLOW}[c]{RESET}  Custom PR number {DIM}(nhập số PR & repo thủ công){RESET}")
        print(f"  {YELLOW}[m]{RESET}  Review NHIỀU PR cùng lúc {DIM}(vd: 1 3 5){RESET}")
        print(f"  {YELLOW}[w]{RESET}  Webhook + Cloudflare Tunnel {DIM}(tức thì từ GitHub){RESET}")
        print(f"  {YELLOW}[p]{RESET}  Polling Daemon {DIM}(tự động quét ngầm){RESET}")
        print(f"  {YELLOW}[r]{RESET}  Refresh danh sách PR")
        print(f"  {YELLOW}[q]{RESET}  Thoát")
        print(f"{BLUE}======================================================================{RESET}")
        print(f"  {DIM}Tip: Nhập số thứ tự [1-{len(pr_options)}] hoặc nhiều số cách nhau bằng dấu cách.{RESET}")

        raw = input(f"\n{BOLD}  >>> {RESET}").strip().lower()

        if raw == "q":
            print(f"\n{GREEN}Tạm biệt! Review well!{RESET}\n")
            sys.exit(0)

        elif raw in ("r", ""):
            continue

        elif raw == "a":
            _add_new_repo(config, repos)

        elif raw == "w":
            _run_webhook_mode(engine, config)

        elif raw == "p":
            _run_polling_mode(engine, state_manager, config, repos, current_user)

        elif raw == "c":
            _run_custom_pr(engine, org, repos_map, repos)

        elif raw == "m":
            _run_multi_pr(engine, pr_options)

        else:
            # Parse space-separated numbers for multi-select or single digit
            tokens = raw.split()
            if all(t.isdigit() for t in tokens) and tokens:
                indices = [int(t) for t in tokens]
                matched = [p for p in pr_options if p["index"] in indices]
                unknown = [i for i in indices if i not in [p["index"] for p in pr_options]]
                if unknown:
                    print(f"  {RED}Số không hợp lệ: {unknown} — chỉ nhập từ danh sách trên.{RESET}")
                    input("  Bấm Enter để tiếp tục...")
                    continue
                if len(matched) == 1:
                    _handle_pr_actions(engine, matched[0])
                elif len(matched) > 1:
                    _run_multi_pr_list(engine, matched)
            else:
                print(f"  {RED}Ký tự không hợp lệ — nhập số từ danh sách, hoặc a/c/m/w/p/r/q.{RESET}")
                input("  Bấm Enter để tiếp tục...")


def _add_new_repo(config: Dict[str, Any], repos: List[str]):
    """Allow user to add any arbitrary GitHub repo to monitor."""
    clear_screen()
    print(f"{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}  THÊM REPOSITORY GITHUB MỚI ĐỂ THEO DÕI{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")
    print("  Ví dụ: owner/repo (như facebook/react, vercel/next.js, deveop-com/clickessms_be)")
    print("  Hoặc dán link GitHub: https://github.com/owner/repo\n")

    while True:
        repo_input = input("  Nhập repo (hoặc Enter để hủy): ").strip()
        if not repo_input:
            return

        # Parse GitHub URL if pasted
        m = re.search(r"github\.com[:/]([\w\-]+)/([\w\-]+?)(?:\.git)?$", repo_input)
        if m:
            clean_repo = f"{m.group(1)}/{m.group(2)}"
        elif "/" in repo_input:
            clean_repo = repo_input
        else:
            print(f"  {RED}Định dạng không đúng. Cần dạng 'owner/repo' (ví dụ: deveop-com/clickessms_be){RESET}")
            continue

        # Check if repo is accessible via gh
        print(f"  {DIM}Đang kiểm tra quyền truy cập repo {clean_repo}...{RESET}")
        res = subprocess.run(["gh", "repo", "view", clean_repo, "--json", "name"], capture_output=True, text=True)
        if res.returncode != 0:
            print(f"  {YELLOW}⚠️ Cảnh báo: gh CLI không đọc được {clean_repo}. Bạn có chắc muốn thêm? (y/N):{RESET} ", end="")
            confirm = input().strip().lower()
            if confirm != "y":
                continue

        if clean_repo not in repos:
            repos.append(clean_repo)
            save_monitored_repos(config, repos)
            print(f"  {GREEN}✅ Đã thêm {clean_repo} vào danh sách theo dõi!{RESET}")
        else:
            print(f"  {YELLOW}Repo {clean_repo} đã có trong danh sách.{RESET}")

        input("\n  Bấm Enter để quay lại menu...")
        break


def _run_multi_pr(engine, pr_options: List[Dict[str, Any]]):
    """Prompt for multi-PR selection."""
    clear_screen()
    print(f"{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}  REVIEW NHIỀU PR CÙNG LÚC{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")
    for p in pr_options:
        print(f"  {YELLOW}[{p['index']:>2}]{RESET}  #{p['number']}  {DIM}{p['repo'].split('/')[-1]}{RESET}  {p['title'][:55]}")

    while True:
        raw = input(f"\n  {BOLD}Nhập số PR (cách nhau bằng dấu cách, vd: 1 3 5):{RESET} ").strip()
        if not raw:
            return
        tokens = raw.split()
        if not all(t.isdigit() for t in tokens):
            print(f"  {RED}Chỉ nhập số, thử lại:{RESET}")
            continue
        indices = [int(t) for t in tokens]
        matched = [p for p in pr_options if p["index"] in indices]
        unknown = set(indices) - {p["index"] for p in pr_options}
        if unknown:
            print(f"  {RED}Số không tồn tại trong danh sách: {sorted(unknown)} — thử lại:{RESET}")
            continue
        break

    _run_multi_pr_list(engine, matched)


def _run_multi_pr_list(engine, prs: List[Dict[str, Any]]):
    """Review a list of PRs sequentially."""
    clear_screen()
    print(f"{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}  CHẠY REVIEW {len(prs)} PR CÙNG LÚC{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")
    for p in prs:
        print(f"  - {p['repo'].split('/')[-1]} #{p['number']}: {p['title'][:60]}")

    confirm = input(f"\n  {BOLD}Xác nhận review {len(prs)} PR trên? (y/N):{RESET} ").strip().lower()
    if confirm != "y":
        print(f"  {YELLOW}Đã huỷ.{RESET}")
        input("  Bấm Enter để quay lại...")
        return

    results = []
    for p in prs:
        print(f"\n{CYAN}{'─'*70}{RESET}")
        print(f"{BOLD}[{prs.index(p)+1}/{len(prs)}] Đang review {p['repo'].split('/')[-1]} PR #{p['number']}...{RESET}")
        try:
            engine.execute_review(p["repo"], p["number"])
            results.append({"pr": p, "status": "OK"})
            print(f"{GREEN}  ✅ Xong PR #{p['number']}{RESET}")
        except Exception as e:
            results.append({"pr": p, "status": f"ERROR: {e}"})
            print(f"{RED}  ❌ Lỗi PR #{p['number']}: {e}{RESET}")

    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}  KẾT QUẢ:{RESET}")
    for r in results:
        status_icon = GREEN + "✅" + RESET if "OK" in r["status"] else RED + "❌" + RESET
        repo_name = r['pr']['repo'].split('/')[-1]
        print(f"  {status_icon}  #{r['pr']['number']} {repo_name} — {r['status']}")
    print(f"{BLUE}{'='*70}{RESET}")
    input("\n  Bấm Enter để quay lại menu chính...")


def _run_custom_pr(engine, org: str, repos_map: Dict[str, str], repos: List[str]):
    """Let user type a PR number manually for any repo."""
    print(f"\n{BOLD}  Nhập thông tin PR:{RESET}")
    while True:
        pr_input = input("    Số PR (ví dụ: 916): ").strip()
        if pr_input.isdigit():
            break
        print(f"    {RED}Chỉ nhập số nguyên dương, thử lại:{RESET}")

    while True:
        default_repo = repos[0] if repos else "owner/repo"
        repo_input = input(f"    Repo (ví dụ 'owner/repo' hoặc 'be'/'fe', mặc định: {default_repo}): ").strip().lower()
        if not repo_input:
            target_repo = default_repo
            break
        if repo_input in repos_map:
            target_repo = f"{org}/{repos_map[repo_input]}"
            break
        elif "/" in repo_input:
            target_repo = repo_input
            break
        else:
            print(f"    {RED}Vui lòng nhập dạng 'owner/repo' (ví dụ: deveop-com/clickessms_be){RESET}")

    _handle_pr_actions(engine, {
        "repo": target_repo,
        "number": int(pr_input),
        "title": f"PR #{pr_input}",
        "author": "manual"
    })


def _run_webhook_mode(engine, config):
    from tunnel_manager import CloudflareTunnel
    from webhook_server import start_webhook_server
    port = config.get("webhook", {}).get("port", 8765)
    tunnel = CloudflareTunnel(port=port)
    tunnel.start()
    try:
        start_webhook_server(port=port, engine=engine, commands=config.get("supported_commands", []))
    except KeyboardInterrupt:
        tunnel.stop()
        print("\n  Webhook stopped.")
        input("  Bấm Enter để quay lại menu...")


def _run_polling_mode(engine, state_manager, config, repos, current_user):
    from polling_daemon import PollingDaemon

    clear_screen()
    print(f"{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}  POLLING DAEMON — CHỌN CHẾ ĐỘ QUÉT{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")
    print(f"  {YELLOW}[1]{RESET}  Quét TOÀN BỘ PR đang mở {DIM}(all open PRs){RESET}")
    if current_user:
        print(f"  {YELLOW}[2]{RESET}  PR cần review bởi bạn {DIM}(reviewer = @{current_user}){RESET}")
        print(f"  {YELLOW}[3]{RESET}  PR được assign cho bạn {DIM}(assignee = @{current_user}){RESET}")
    print(f"  {YELLOW}[b]{RESET}  Quay lại\n")
    print(f"  {DIM}Giải thích:")
    print(f"     [2] Reviewer = team lead request bạn review PR đó{RESET}")
    print(f"  {DIM}  [3] Assignee = bạn được giao xử lý / owner PR đó{RESET}\n")

    while True:
        sub = input(f"  {BOLD}Lựa chọn:{RESET} ").strip().lower()
        if sub == "b":
            return
        if sub == "1":
            assigned_filter = None
            reviewer_filter = None
            break
        if sub == "2" and current_user:
            assigned_filter = None
            reviewer_filter = current_user
            break
        if sub == "3" and current_user:
            assigned_filter = current_user
            reviewer_filter = None
            break
        print(f"  {RED}Không hợp lệ, thử lại:{RESET}")

    interval = config.get("poll_interval_seconds", 60)
    daemon = PollingDaemon(
        repos=repos,
        engine=engine,
        state_manager=state_manager,
        interval=interval,
        assigned_filter=assigned_filter,
        reviewer_filter=reviewer_filter
    )
    if reviewer_filter:
        mode_label = f"PRs requested to review by @{reviewer_filter}"
    elif assigned_filter:
        mode_label = f"PRs assigned to @{assigned_filter}"
    else:
        mode_label = "all open PRs"

    print(f"\n  {GREEN}Polling Daemon STARTED{RESET}")
    print(f"  Mode     : {CYAN}{mode_label}{RESET}")
    print(f"  Interval : every {interval}s")
    print(f"  {YELLOW}[!] Để DỪNG Polling: nhấn Ctrl+C{RESET}\n")
    try:
        daemon.start()
    except KeyboardInterrupt:
        print(f"\n  {YELLOW}Polling Daemon đã dừng.{RESET}")
        input("  Bấm Enter để quay lại menu...")


def _handle_pr_actions(engine, pr_info: Dict[str, Any]):
    repo = pr_info["repo"]
    number = pr_info["number"]
    title = pr_info["title"]

    while True:
        clear_screen()
        repo_short = repo.split("/")[-1]
        print(f"{BLUE}{'='*70}{RESET}")
        print(f"{GREEN}{BOLD}    [{repo_short.upper()} #{number}]{RESET}  {CYAN}{title}{RESET}")
        print(f"{BLUE}{'='*70}{RESET}")
        print(f"\n  {YELLOW}[1]{RESET}  Review toàn diện {DIM}(Google Standards + Dashboard + In-line){RESET}  {GREEN}[mặc định]{RESET}")
        print(f"  {YELLOW}[2]{RESET}  Re-review {DIM}(chỉ so sánh commit mới nhất vs lần review trước){RESET}")
        print(f"  {YELLOW}[3]{RESET}  Mở PR trên trình duyệt (GitHub Web)")
        print(f"  {YELLOW}[b]{RESET}  Quay lại danh sách PR")
        print(f"{BLUE}{'='*70}{RESET}")

        while True:
            sub = input(f"\n  {BOLD}>>> {RESET}").strip().lower()
            if sub in ("", "1", "2", "3", "b"):
                break
            print(f"  {RED}Chỉ nhập 1/2/3/b, thử lại:{RESET}")

        if sub == "b":
            break

        if sub in ("", "1", "2"):
            action_label = "Re-review" if sub == "2" else "Review toàn diện"
            print(f"\n  {GREEN}{action_label} {repo_short} PR #{number}...{RESET}\n")
            try:
                engine.execute_review(repo, number)
                print(f"\n  {GREEN}✅ Hoàn thành! Kết quả đã được gửi lên GitHub.{RESET}\n")
            except Exception as e:
                print(f"\n  {RED}❌ Lỗi: {e}{RESET}\n")

            while True:
                ask_web = input("  Mở PR trên trình duyệt để xem kết quả? (y/N): ").strip().lower()
                if ask_web in ("y", "n", ""):
                    break
                print(f"  {RED}Chỉ nhập y hoặc N:{RESET}")
            if ask_web == "y":
                open_pr_in_browser(repo, number)
            input("\n  Bấm Enter để quay lại menu chính...")
            break

        elif sub == "3":
            print(f"\n  {BLUE}Đang mở PR #{number} trên trình duyệt...{RESET}")
            open_pr_in_browser(repo, number)
            input("  Bấm Enter để tiếp tục...")
