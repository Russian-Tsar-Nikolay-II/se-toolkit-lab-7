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
            labs = []
            for item in data:
                item_type = item.get("type", "")
                item_id = str(item.get("id", ""))
                if item_type == "lab" or "lab" in item_id.lower():
                    labs.append(item)
            if not labs:
                labs = data
            lines = ["Available labs:"]
            for lab in labs:
                lab_id = lab.get("id", "unknown")
                title = lab.get("title", lab.get("name", "Untitled"))
                lines.append(f"- Lab {lab_id} — {title}")
            return "\n".join(lines)
    except httpx.ConnectError:
        return "Backend error: connection refused (localhost:42002). Check that the services are running."
    except httpx.HTTPStatusError as e:
        return f"Backend error: HTTP {e.response.status_code} {e.response.reason_phrase}. The backend service may be down."
    except Exception as e:
        return f"Backend error: {type(e).__name__}: {str(e)}"
