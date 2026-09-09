import os
import json
import time
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List

ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

def load_env_keys() -> Dict[str, str]:
    keys = {}
    if os.path.exists(ENV_FILE):
        try:
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        keys[k.strip()] = v.strip()
        except Exception:
            pass
    return keys

class LLMClient:
    """Universal LLM client supporting Gemini, DeepSeek, and OpenAI with zero external dependencies."""

    def __init__(self, provider: str = "gemini", api_key: str = "", model: str = ""):
        self.provider = provider.lower()
        env_keys = load_env_keys()

        if not api_key:
            if self.provider == "gemini":
                api_key = env_keys.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY", "")
            elif self.provider == "deepseek":
                api_key = env_keys.get("DEEPSEEK_API_KEY") or os.environ.get("DEEPSEEK_API_KEY", "")
            elif self.provider == "openai":
                api_key = env_keys.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY", "")

        self.api_key = api_key
        self.model = model or self._default_model(self.provider)

    def _default_model(self, provider: str) -> str:
        if provider == "gemini":
            return "gemini-3.8-flash"
        elif provider == "deepseek":
            return "deepseek-reasoner"
        elif provider == "openai":
            return "gpt-5"
        return "gemini-3.8-flash"

    def is_configured(self) -> bool:
        return bool(self.api_key and self.provider in ["gemini", "deepseek", "openai"])

    def generate_review(self, pr_meta: Dict[str, Any], diff: str, rules_summary: str) -> Optional[str]:
        """Generate full code review markdown from LLM."""
        if not self.is_configured():
            return None

        system_instruction = (
            "You are a Principal Tech Lead conducting an automated code review adhering to Google Engineering Practices.\n"
            "Analyze the code changes (git diff) against the provided rules, find bugs, security risks, N+1 queries, "
            "performance bottlenecks, styling nits, and edge-cases.\n\n"
            "### BUNDLED RULES & CRITERIA:\n"
            f"{rules_summary}\n\n"
            "### OUTPUT FORMAT INSTRUCTIONS:\n"
            "Your output MUST be strictly formatted GitHub Markdown with:\n"
            "1. Header with Reviewed Commit, Type, Effort Score (⭐ 1-5).\n"
            "2. '### 📊 Overview Dashboard' table with exact counts of 🔴 Critical, 🟡 Major, 🟢 Minor, 💡 Suggestions, and Nit: Style, plus a Verdict (🟢 APPROVE, 🟡 COMMENT, or 🔴 REQUEST_CHANGES).\n"
            "3. Detailed sections for findings with file:line, Why explanation, and GitHub Suggestion code blocks (```suggestion ... ```).\n"
            "4. '### 📋 Google Review Checklist' table covering Design, Functionality, Complexity, Security, Tests, Style.\n"
            "Do NOT wrap your entire response in triple backticks. Provide clean Markdown directly."
        )

        user_content = (
            f"PR Title: {pr_meta.get('title', '')}\n"
            f"PR Author: @{pr_meta.get('author', {}).get('login', 'unknown')}\n"
            f"PR Number: #{pr_meta.get('number', '')}\n"
            f"Base Branch: {pr_meta.get('baseRefName', '')} <- Head: {pr_meta.get('headRefName', '')}\n\n"
            f"DIFF:\n```diff\n{diff[:50000]}\n```"
        )

        try:
            if self.provider == "gemini":
                return self._call_gemini(system_instruction, user_content)
            elif self.provider in ["deepseek", "openai"]:
                return self._call_openai_compatible(system_instruction, user_content)
        except Exception as e:
            print(f"⚠️  LLM API error ({self.provider}): {e}")
            return None

    def _call_gemini(self, system_prompt: str, user_prompt: str, max_retries: int = 2) -> str:
        """Call Gemini API with smart fallback chain.

        Distinguishes:
        - 429 RESOURCE_EXHAUSTED (daily quota) → no retry, skip to next model immediately
        - 429 transient rate-limit              → retry with backoff
        - 503 server overload                   → retry with backoff
        - Other errors                          → fail fast
        """
        # Build fallback chain: 3.8→3.6 for high-demand models
        models_to_try = [self.model]
        if self.model in ["gemini-3.8-flash", "gemini-3.7-flash"] and "gemini-3.6-flash" not in models_to_try:
            models_to_try.append("gemini-3.6-flash")

        last_error = None
        for model_idx, current_model in enumerate(models_to_try):
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{current_model}:generateContent?key={self.api_key}"
            )
            payload = {
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"parts": [{"text": user_prompt}]}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 8192},
            }
            data_bytes = json.dumps(payload).encode("utf-8")

            model_failed = False
            for attempt in range(1, max_retries + 1):
                try:
                    req = urllib.request.Request(
                        url,
                        data=data_bytes,
                        headers={"Content-Type": "application/json"},
                    )
                    with urllib.request.urlopen(req, timeout=90) as resp:
                        result = json.loads(resp.read().decode("utf-8"))
                        candidates = result.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                if current_model != self.model:
                                    print(
                                        f"  💡 [Gemini Auto-Fallback] Phản hồi thành công từ: {current_model}"
                                    )
                                return parts[0].get("text", "")
                    raise RuntimeError(f"No text returned by Gemini API ({current_model})")

                except urllib.error.HTTPError as err:
                    err_body = ""
                    try:
                        err_body = err.read().decode("utf-8")
                    except Exception:
                        pass

                    if err.code == 429:
                        # Distinguish quota-exhausted (daily cap) vs transient rate-limit spike
                        is_quota_exhausted = (
                            "RESOURCE_EXHAUSTED" in err_body
                            or "quota" in err_body.lower()
                            or "GenerateRequestsPerDay" in err_body
                        )
                        if is_quota_exhausted:
                            # Daily quota cạn → KHÔNG retry (retry cũng vô ích, cần chờ 24h)
                            print(
                                f"  🚫 [{current_model}] Quota ngày đã cạn "
                                f"(429 RESOURCE_EXHAUSTED). Bỏ qua, không retry."
                            )
                            last_error = RuntimeError(
                                f"QUOTA_EXHAUSTED:{current_model} - {err_body[:200]}"
                            )
                            model_failed = True
                            break  # Jump to next model immediately

                        # Transient 429 (rate-limit spike) → retry with backoff
                        if attempt < max_retries:
                            wait_sec = attempt * 2
                            print(
                                f"  ⏳ [Gemini 429] {current_model} tạm thời bận, "
                                f"thử lại sau {wait_sec}s (Lần {attempt}/{max_retries})..."
                            )
                            time.sleep(wait_sec)
                            continue

                        print(
                            f"  ⚠️ [{current_model}] Hết lượt retry (429). "
                            f"Chuyển sang model tiếp theo..."
                        )
                        last_error = RuntimeError(f"HTTP 429: {err.reason} - {err_body[:200]}")
                        model_failed = True
                        break

                    elif err.code == 503:
                        # Server overload → retry is meaningful
                        if attempt < max_retries:
                            wait_sec = attempt * 2
                            print(
                                f"  ⏳ [Gemini 503] {current_model} quá tải, "
                                f"thử lại sau {wait_sec}s (Lần {attempt}/{max_retries})..."
                            )
                            time.sleep(wait_sec)
                            continue
                        print(
                            f"  ⚠️ [{current_model}] Server vẫn quá tải sau "
                            f"{max_retries} lần thử. Chuyển sang model tiếp theo..."
                        )
                        last_error = RuntimeError(f"HTTP 503: {err.reason} - {err_body[:200]}")
                        model_failed = True
                        break

                    else:
                        # Other HTTP errors (400, 401, etc.) → fail immediately
                        last_error = RuntimeError(
                            f"HTTP {err.code}: {err.reason} - {err_body[:200]}"
                        )
                        model_failed = True
                        break

                except Exception as e:
                    last_error = e
                    if attempt < max_retries:
                        time.sleep(2)
                        continue
                    model_failed = True
                    break

            if not model_failed:
                break  # Successful return happened inside the loop

            # Announce next fallback model if available
            if model_idx + 1 < len(models_to_try):
                print(f"  🔄 Đang thử model dự phòng: {models_to_try[model_idx + 1]}...")

        if last_error:
            raise last_error
        raise RuntimeError("No response from Gemini API after all models failed.")

    def _call_openai_compatible(self, system_prompt: str, user_prompt: str, max_retries: int = 3) -> str:
        if self.provider == "deepseek":
            endpoint = "https://api.deepseek.com/v1/chat/completions"
        else:
            endpoint = "https://api.openai.com/v1/chat/completions"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2
        }
        data_bytes = json.dumps(payload).encode("utf-8")

        for attempt in range(1, max_retries + 1):
            try:
                req = urllib.request.Request(
                    endpoint,
                    data=data_bytes,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}"
                    }
                )
                with urllib.request.urlopen(req, timeout=90) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    choices = data.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "")
                raise RuntimeError(f"No response returned from {self.provider} API")
            except urllib.error.HTTPError as err:
                if err.code in [503, 429, 500] and attempt < max_retries:
                    wait_sec = attempt * 2
                    print(f"  ⏳ [{self.provider.upper()} {err.code}] Server busy, retrying in {wait_sec}s (Attempt {attempt}/{max_retries})...")
                    time.sleep(wait_sec)
                    continue
                err_body = ""
                try:
                    err_body = err.read().decode("utf-8")
                except Exception:
                    pass
                raise RuntimeError(f"HTTP {err.code}: {err.reason} - {err_body[:200]}")
            except Exception as e:
                if attempt < max_retries:
                    time.sleep(2)
                    continue
                raise
