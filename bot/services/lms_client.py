from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse

import httpx


def _load_env_file(path: Path) -> None:
    if not path.is_file():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key and key not in os.environ:
            os.environ[key] = value


def load_env() -> None:
    bot_dir = Path(__file__).resolve().parents[1]
    repo_dir = bot_dir.parent

    for candidate in (
        repo_dir / ".env.bot.secret",
        repo_dir / ".env.docker.secret",
        bot_dir / ".env",
        bot_dir / ".env.example",
    ):
        _load_env_file(candidate)


load_env()


class LMSClient:
    def __init__(self) -> None:
        self.base_url = os.getenv("LMS_API_BASE_URL", "http://localhost:42002").rstrip("/")
        self.api_key = os.getenv("LMS_API_KEY", "")

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _host_port(self) -> str:
        parsed = urlparse(self.base_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        return f"{host}:{port}"

    def _error_message(self, exc: Exception) -> str:
        if isinstance(exc, httpx.HTTPStatusError):
            status = exc.response.status_code
            reason = exc.response.reason_phrase
            return f"HTTP {status} {reason}. The backend service may be down."

        if isinstance(exc, httpx.ConnectError):
            details = str(exc).strip()
            if details and details != "All connection attempts failed":
                return f"connection refused ({self._host_port()}): {details}. Check that the services are running."
            return f"connection refused ({self._host_port()}). Check that the services are running."

        if isinstance(exc, httpx.TimeoutException):
            return f"request timed out while contacting {self._host_port()}. Check that the backend is running and reachable."

        if isinstance(exc, httpx.RequestError):
            details = str(exc).strip() or exc.__class__.__name__
            return f"request error while contacting {self._host_port()}: {details}."

        if isinstance(exc, ValueError):
            return f"invalid JSON from backend: {exc}"

        return str(exc)

    def _get(self, path: str, params: dict[str, str] | None = None) -> list[dict] | dict[str, str]:
        try:
            with httpx.Client(base_url=self.base_url, timeout=5.0, follow_redirects=True) as client:
                response = client.get(path, params=params, headers=self._headers())
                response.raise_for_status()
                data = response.json()
                if isinstance(data, list):
                    return data
                return {"error": f"unexpected backend response type: {type(data).__name__}"}
        except Exception as exc:
            return {"error": self._error_message(exc)}

    def get_items(self) -> list[dict] | dict[str, str]:
        return self._get("/items/")

    def get_pass_rates(self, lab_slug: str) -> list[dict] | dict[str, str]:
        return self._get("/analytics/pass-rates", params={"lab": lab_slug})
