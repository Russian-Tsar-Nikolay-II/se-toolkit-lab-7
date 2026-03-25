import os
import httpx

LMS_BASE_URL = os.getenv("LMS_API_BASE_URL", "http://localhost:42002")
LMS_API_KEY = os.getenv("LMS_API_KEY", "")

def get_headers():
    headers = {}
    if LMS_API_KEY:
        headers["Authorization"] = f"Bearer {LMS_API_KEY}"
    return headers

def format_error(e: Exception) -> str:
    if isinstance(e, httpx.ConnectError):
        return "connection refused. Check that backend is running."
    if isinstance(e, httpx.HTTPStatusError):
        return f"HTTP {e.response.status_code} {e.response.reason_phrase}. The backend may be down."
    return str(e)

class LMSClient:
    def __init__(self):
        self.base_url = LMS_BASE_URL

    def get_items(self):
        try:
            r = httpx.get(f"{self.base_url}/items/", headers=get_headers(), timeout=5)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"error": format_error(e)}

    def get_pass_rates(self, lab_id: str):
        try:
            r = httpx.get(
                f"{self.base_url}/analytics/pass-rates",
                params={"lab": lab_id},
                headers=get_headers(),
                timeout=5
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"error": format_error(e)}
