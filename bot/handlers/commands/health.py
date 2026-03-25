import httpx
import os

async def handle_health(args=None):
    api_key = os.getenv("LMS_API_KEY", "YOUR_LMS_API_KEY")
    url = "http://localhost:42002/items/"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
            count = len(data) if isinstance(data, list) else 0
            return f"Health check OK: {count} items"
    except httpx.ConnectError:
        return "Backend error: connection refused (localhost:42002). Check that the services are running."
    except httpx.HTTPStatusError as e:
        return f"Backend error: HTTP {e.response.status_code} {e.response.reason_phrase}. The backend service may be down."
    except Exception as e:
        return f"Backend error: {type(e).__name__}: {str(e)}"
