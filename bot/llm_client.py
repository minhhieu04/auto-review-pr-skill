import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List

class LLMClient:
    """Universal LLM client supporting Gemini, DeepSeek, and OpenAI with zero external dependencies."""

    def __init__(self, provider: str = "gemini", api_key: str = "", model: str = ""):
        self.provider = provider.lower()
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY") or os.environ.get("DEEPSEEK_API_KEY") or ""
        self.model = model or self._default_model(self.provider)

    def _default_model(self, provider: str) -> str:
        if provider == "gemini":
            return "gemini-2.5-flash"
        elif provider == "deepseek":
            return "deepseek-chat"
        elif provider == "openai":
            return "gpt-4o-mini"
        return "gemini-2.5-flash"

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
            f"DIFF:\n```diff\n{diff[:50000]}\n```"  # Send up to 50k chars
        )

        try:
            if self.provider == "gemini":
                return self._call_gemini(system_instruction, user_content)
            elif self.provider in ["deepseek", "openai"]:
                return self._call_openai_compatible(system_instruction, user_content)
        except Exception as e:
            print(f"⚠️  LLM API error ({self.provider}): {e}")
            return None

    def _call_gemini(self, system_prompt: str, user_prompt: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [
                {
                    "parts": [{"text": user_prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 8192
            }
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
        raise RuntimeError("No text returned by Gemini API")

    def _call_openai_compatible(self, system_prompt: str, user_prompt: str) -> str:
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
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
        raise RuntimeError(f"No response returned from {self.provider} API")
