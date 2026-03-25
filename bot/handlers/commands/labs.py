import httpx
import os

async def handle_labs(args=None):
    api_key = os.getenv("LMS_API_KEY", "YOUR_LMS_API_KEY")
    url = "http://localhost:42002/items/"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
            labs = [item for item in data if item.get("type") == "lab"]
            if not labs:
                labs = [item for item in data if "lab" in str(item.get("id", "")).lower()]
            lines = ["Available labs:"]
            for lab in labs:
                title = lab.get("title", lab.get("name", "Untitled"))
                # Формат: "- Lab 01 — Products, Architecture & Roles"
                lines.append(f"- {title}")
            return "\n".join(lines)
    except httpx.ConnectError:
        return "Backend error: connection refused (localhost:42002). Check that the services are running."
    except httpx.HTTPStatusError as e:
        return f"Backend error: HTTP {e.response.status_code} {e.response.reason_phrase}. The backend service may be down."
    except Exception as e:
        return f"Backend error: {type(e).__name__}: {str(e)}"
