import subprocess
import shutil
import re
import threading
import time
from typing import Optional

class CloudflareTunnel:
    def __init__(self, port: int = 8765):
        self.port = port
        self.process: Optional[subprocess.Popen] = None
        self.public_url: Optional[str] = None
        self._stop_event = threading.Event()

    @staticmethod
    def is_installed() -> bool:
        return shutil.which("cloudflared") is not None

    def start(self) -> Optional[str]:
        if not self.is_installed():
            print("\n❌ cloudflared is not installed!")
            print("👉 Install it quickly with Homebrew:")
            print("   brew install cloudflared\n")
            return None

        cmd = ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{self.port}"]
        print(f"🚀 Starting Cloudflare Tunnel on port {self.port}...")

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
        except Exception as e:
            print(f"❌ Failed to start cloudflared: {e}")
            return None

        # Reader thread to extract public URL from stderr
        def _read_output():
            pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
            while not self._stop_event.is_set() and self.process and self.process.stderr:
                line = self.process.stderr.readline()
                if not line:
                    break
                match = pattern.search(line)
                if match:
                    self.public_url = match.group(0)
                    print("\n" + "=" * 65)
                    print(f"🌐 Cloudflare Tunnel is LIVE!")
                    print(f"   Public Webhook URL: {self.public_url}/webhook")
                    print("=" * 65)
                    print("\n📋 GITHUB WEBHOOK SETUP INSTRUCTIONS:")
                    print(f"   1. Go to your GitHub Repo -> Settings -> Webhooks -> Add webhook")
                    print(f"   2. Payload URL : {self.public_url}/webhook")
                    print(f"   3. Content type: application/json")
                    print(f"   4. Events: Select 'Pull requests' and 'Issue comments'")
                    print("=" * 65 + "\n")

        thread = threading.Thread(target=_read_output, daemon=True)
        thread.start()

        # Wait up to 15 seconds for URL
        for _ in range(30):
            if self.public_url:
                return self.public_url
            time.sleep(0.5)

        return self.public_url

    def stop(self) -> None:
        self._stop_event.set()
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
            print("⏹️ Cloudflare Tunnel stopped.")
