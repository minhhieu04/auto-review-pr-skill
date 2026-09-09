import os
import sys
import json
import re
import subprocess
from typing import List, Dict, Any, Optional, Tuple

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

def get_gh_accounts() -> Tuple[List[str], Optional[str]]:
    """Detect all logged in accounts from gh auth status and the active account."""
    accounts = []
    active_user = None
    try:
        res = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
        out = res.stdout + "\n" + res.stderr
        current_acc = None
        for line in out.splitlines():
            m = re.search(r"account\s+([\w\-]+)", line)
            if m:
                current_acc = m.group(1)
                if current_acc not in accounts:
                    accounts.append(current_acc)
            if "Active account: true" in line and current_acc:
                active_user = current_acc
    except Exception:
        pass
    if not active_user and accounts:
        active_user = accounts[0]
    return accounts, active_user

def fetch_user_repos(limit: int = 25) -> List[Dict[str, Any]]:
    """Fetch repos accessible to the currently active GitHub user."""
    try:
        res = subprocess.run([
            "gh", "repo", "list",
            "--limit", str(limit),
            "--json", "nameWithOwner,isPrivate,description,updatedAt"
        ], capture_output=True, text=True, check=True)
        return json.loads(res.stdout)
    except Exception as e:
        print(f"{YELLOW}⚠️ Cannot fetch user repos: {e}{RESET}")
        return []

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

    # Auto-detect repo if running inside a git directory
    detected_repo = detect_current_repo()
    if detected_repo and detected_repo not in repos:
        repos.insert(0, detected_repo)

    if not repos:
        repos = ["deveop-com/clickessms_be", "deveop-com/clickessms_fe"]

    while True:
        clear_screen()
        accounts, current_user = get_gh_accounts()

        print(f"{BLUE}======================================================================{RESET}")
        print(f"{GREEN}{BOLD}    ANTIGRAVITY & PR-AGENT — UNIVERSAL CODE REVIEW DASHBOARD{RESET}")
        print(f"{BLUE}======================================================================{RESET}")

        header_info = []
        if current_user:
            acc_count_badge = f" ({len(accounts)} accounts)" if len(accounts) > 1 else ""
            header_info.append(f"Git User: {CYAN}@{current_user}{RESET}{DIM}{acc_count_badge}{RESET}")
        if detected_repo:
            header_info.append(f"Current Dir: {GREEN}{detected_repo}{RESET}")
        if header_info:
            print(f"  {' | '.join(header_info)}")
            print(f"  {DIM}Loading open PRs...{RESET}")

        pr_options: List[Dict[str, Any]] = []
        option_index = 1

        for repo in repos:
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

        ai_conf = config.get("ai", {})
        prov_name = ai_conf.get("provider", "gemini").upper()
        has_api_key = bool(ai_conf.get("api_key") or os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY") or os.environ.get("DEEPSEEK_API_KEY"))
        ai_badge = f"{GREEN}AI ON ({prov_name}){RESET}" if has_api_key else f"{DIM}Local Subagents (No API Key){RESET}"

        print(f"\n{BLUE}  {'─' * 66}{RESET}")
        print(f"{BOLD}  OTHER OPTIONS:{RESET}")
        print(f"  {YELLOW}[k]{RESET}  Cài đặt AI Engine & API Key {DIM}(Gemini / DeepSeek / ChatGPT){RESET} [{ai_badge}]")
        print(f"  {YELLOW}[s]{RESET}  Chọn từ Repos của tôi {DIM}(Browse & Select My GitHub Repos){RESET}")
        print(f"  {YELLOW}[u]{RESET}  Chuyển Git User {DIM}(Switch Active GitHub Account: {len(accounts)} available){RESET}")
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

        elif raw == "k":
            _manage_ai_settings(config, engine)

        elif raw == "s":
            _browse_and_select_my_repos(config, repos)

        elif raw == "u":
            _switch_gh_user(accounts, current_user)

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
                print(f"  {RED}Ký tự không hợp lệ — nhập số từ danh sách, hoặc s/u/a/c/m/w/p/r/q.{RESET}")
                input("  Bấm Enter để tiếp tục...")


def _manage_ai_settings(config: Dict[str, Any], engine):
    """View and configure AI Provider, Model, and API Key."""
    ai_conf = config.setdefault("ai", {})
    from llm_client import LLMClient

    while True:
        clear_screen()
        provider = ai_conf.get("provider", "gemini").lower()
        model = ai_conf.get("model", "") or ("gemini-3.8-flash" if provider == "gemini" else "deepseek-reasoner" if provider == "deepseek" else "gpt-4o")
        raw_key = ai_conf.get("api_key", "") or os.environ.get("GEMINI_API_KEY", "") or os.environ.get("OPENAI_API_KEY", "") or os.environ.get("DEEPSEEK_API_KEY", "")
        masked_key = (raw_key[:6] + "..." + raw_key[-4:]) if len(raw_key) > 10 else ("Chưa có" if not raw_key else "******")
        status = f"{GREEN}BẬT (Active){RESET}" if raw_key else f"{YELLOW}TẮT (Đang dùng 4 Subagents Rule-based cục bộ){RESET}"

        print(f"{BLUE}{'='*70}{RESET}")
        print(f"{BOLD}  🤖 CÀI ĐẶT AI REVIEW ENGINE & API KEY{RESET}")
        print(f"{BLUE}{'='*70}{RESET}")
        print(f"  Provider hiện tại : {CYAN}{provider.upper()}{RESET}")
        print(f"  Model hiện tại    : {BOLD}{model}{RESET}")
        print(f"  API Key           : {masked_key}")
        print(f"  Trạng thái AI     : {status}\n")

        print("  Các tùy chọn:")
        print(f"    {YELLOW}[1]{RESET}  Đổi Provider (1: Google Gemini | 2: DeepSeek | 3: OpenAI)")
        print(f"    {YELLOW}[2]{RESET}  Nhập / Đổi API Key")
        print(f"    {YELLOW}[3]{RESET}  Đổi tên Model (ví dụ: gemini-3.8-flash, gemini-3.8-pro, deepseek-reasoner, gpt-4o)")
        print(f"    {YELLOW}[4]{RESET}  ⚡ Test kết nối AI (gửi ping test)")
        print(f"    {YELLOW}[5]{RESET}  Xóa API Key (quay về chế độ Local Subagents)")
        print(f"    {YELLOW}[b]{RESET}  Lưu & Quay lại menu chính\n")

        sub = input(f"  {BOLD}Chọn thao tác [1-5/b]:{RESET} ").strip().lower()
        if sub in ("b", ""):
            engine.llm_client = LLMClient(
                provider=ai_conf.get("provider", "gemini"),
                api_key=ai_conf.get("api_key", ""),
                model=ai_conf.get("model", "")
            )
            try:
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"  {YELLOW}Không thể lưu file config: {e}{RESET}")
            return

        elif sub == "1":
            print("\n  Chọn Provider:")
            print("    [1] Google Gemini (Mặc định: gemini-3.8-flash)")
            print("    [2] DeepSeek (Mặc định: deepseek-reasoner / deepseek-chat)")
            print("    [3] OpenAI / ChatGPT (Mặc định: gpt-5 / gpt-4o)")
            p_choice = input("  Chọn [1-3]: ").strip()
            if p_choice == "1":
                ai_conf["provider"] = "gemini"
                ai_conf["model"] = "gemini-3.8-flash"
            elif p_choice == "2":
                ai_conf["provider"] = "deepseek"
                ai_conf["model"] = "deepseek-reasoner"
            elif p_choice == "3":
                ai_conf["provider"] = "openai"
                ai_conf["model"] = "gpt-5"

        elif sub == "2":
            key_input = input(f"\n  Dán {provider.upper()} API Key của bạn: ").strip()
            if key_input:
                ai_conf["api_key"] = key_input
                print(f"  {GREEN}✅ Đã lưu API Key!{RESET}")
                input("  Bấm Enter để tiếp tục...")

        elif sub == "3":
            model_input = input(f"\n  Nhập tên model (hiện tại: {model}): ").strip()
            if model_input:
                ai_conf["model"] = model_input
                print(f"  {GREEN}✅ Đã cập nhật model thành {model_input}!{RESET}")
                input("  Bấm Enter để tiếp tục...")

        elif sub == "4":
            print(f"\n  {CYAN}Đang test kết nối tới {provider.upper()} API...{RESET}")
            test_client = LLMClient(
                provider=ai_conf.get("provider", "gemini"),
                api_key=ai_conf.get("api_key", ""),
                model=ai_conf.get("model", "")
            )
            if not test_client.is_configured():
                print(f"  {RED}Chưa cấu hình API Key. Vui lòng nhập key ở tùy chọn [2].{RESET}")
            else:
                try:
                    res = test_client.generate_review(
                        {"title": "Test Ping", "number": 1, "author": {"login": "test"}, "baseRefName": "main", "headRefName": "test"},
                        "+ def ping():\n+     return 'pong'",
                        "Ping test only."
                    )
                    if res:
                        print(f"  {GREEN}✅ Kết nối AI thành công! Model {model} phản hồi tốt.{RESET}")
                    else:
                        print(f"  {RED}❌ Không nhận được phản hồi từ AI.{RESET}")
                except Exception as err:
                    print(f"  {RED}❌ Lỗi kết nối: {err}{RESET}")
            input("  Bấm Enter để tiếp tục...")

        elif sub == "5":
            ai_conf["api_key"] = ""
            print(f"  {YELLOW}Đã xóa API Key. Hệ thống sẽ dùng bộ 4 Subagents Rule-based cục bộ.{RESET}")
            input("  Bấm Enter để tiếp tục...")


def _switch_gh_user(accounts: List[str], current_user: Optional[str]):
    """Switch active GitHub user account using gh auth switch."""
    clear_screen()
    print(f"{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}  CHUYỂN TÀI KHOẢN GITHUB ACTIVE (MULTI-ACCOUNT SWITCHER){RESET}")
    print(f"{BLUE}{'='*70}{RESET}")

    if not accounts:
        print(f"  {YELLOW}Chưa phát hiện tài khoản GitHub nào đăng nhập qua gh CLI.{RESET}")
        print("  Để đăng nhập, chạy: gh auth login")
        input("\n  Bấm Enter để quay lại...")
        return

    print(f"  Tài khoản đang active: {GREEN}@{current_user}{RESET}\n")
    print("  Danh sách tài khoản trên máy:")
    for idx, acc in enumerate(accounts, 1):
        is_active = f" {GREEN}[ACTIVE]{RESET}" if acc == current_user else ""
        print(f"    {YELLOW}[{idx}]{RESET} @{acc}{is_active}")

    print(f"\n  {DIM}Tip: Để thêm tài khoản mới vào máy, chạy 'gh auth login' trong terminal.{RESET}")
    print("  Nhập số thứ tự tài khoản muốn chuyển sang (hoặc Enter để hủy):")

    while True:
        choice = input(f"\n  {BOLD}Chọn tài khoản [1-{len(accounts)}]:{RESET} ").strip()
        if not choice:
            return
        if choice.isdigit() and 1 <= int(choice) <= len(accounts):
            target_user = accounts[int(choice) - 1]
            if target_user == current_user:
                print(f"  {YELLOW}Tài khoản @{target_user} đã là active rồi!{RESET}")
                input("  Bấm Enter để quay lại...")
                return
            print(f"\n  {CYAN}Đang chuyển active account sang @{target_user}...{RESET}")
            res = subprocess.run(["gh", "auth", "switch", "--user", target_user], capture_output=True, text=True)
            if res.returncode == 0:
                print(f"  {GREEN}✅ Đã chuyển thành công sang tài khoản @{target_user}!{RESET}")
            else:
                print(f"  {RED}Lỗi khi chuyển tài khoản: {res.stderr}{RESET}")
            input("\n  Bấm Enter để quay lại menu...")
            return
        print(f"  {RED}Lựa chọn không hợp lệ, vui lòng thử lại.{RESET}")


def _browse_and_select_my_repos(config: Dict[str, Any], repos: List[str]):
    """Browse repos of the active user and add to monitored list."""
    clear_screen()
    print(f"{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}  DANH SÁCH REPOSITORIES CỦA BẠN (GITHUB REPO BROWSER){RESET}")
    print(f"{BLUE}{'='*70}{RESET}")
    print(f"  {DIM}Đang tải danh sách repo từ GitHub...{RESET}\n")

    user_repos = fetch_user_repos(limit=30)
    if not user_repos:
        print(f"  {YELLOW}Không tìm thấy repo nào hoặc không thể kết nối GitHub.{RESET}")
        input("\n  Bấm Enter để quay lại...")
        return

    for idx, r in enumerate(user_repos, 1):
        badge = f"{MAGENTA}[private]{RESET}" if r.get("isPrivate") else f"{DIM}[public]{RESET}"
        name = r["nameWithOwner"]
        is_monitored = f" {GREEN}✓ đang theo dõi{RESET}" if name in repos else ""
        print(f"  {YELLOW}[{idx:>2}]{RESET} {name:<40} {badge}{is_monitored}")

    print(f"\n{BLUE}  {'─' * 66}{RESET}")
    print(f"  {DIM}Nhập số thứ tự để THÊM vào danh sách theo dõi (nhập nhiều số cách nhau bằng dấu cách).{RESET}")
    choice = input(f"  {BOLD}Chọn repo [1-{len(user_repos)}] (hoặc Enter để hủy):{RESET} ").strip()
    if not choice:
        return

    tokens = choice.split()
    if all(t.isdigit() for t in tokens):
        added = []
        for t in tokens:
            val = int(t)
            if 1 <= val <= len(user_repos):
                picked_name = user_repos[val - 1]["nameWithOwner"]
                if picked_name not in repos:
                    repos.append(picked_name)
                    added.append(picked_name)
        if added:
            save_monitored_repos(config, repos)
            print(f"\n  {GREEN}✅ Đã thêm {len(added)} repo vào danh sách theo dõi: {', '.join(added)}{RESET}")
        else:
            print(f"\n  {YELLOW}Các repo đã chọn đều đã có trong danh sách.{RESET}")
    else:
        print(f"  {RED}Lựa chọn không hợp lệ.{RESET}")

    input("\n  Bấm Enter để quay lại menu...")


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

        m = re.search(r"github\.com[:/]([\w\-]+)/([\w\-]+?)(?:\.git)?$", repo_input)
        if m:
            clean_repo = f"{m.group(1)}/{m.group(2)}"
        elif "/" in repo_input:
            clean_repo = repo_input
        else:
            print(f"  {RED}Định dạng không đúng. Cần dạng 'owner/repo' (ví dụ: deveop-com/clickessms_be){RESET}")
            continue

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
