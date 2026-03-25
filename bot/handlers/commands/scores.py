import httpx
import os

async def handle_scores(args=None):
    if not args or not isinstance(args, list) or len(args) == 0:
        return "Usage: /scores <lab-id>. Example: /scores lab-04"
    lab_id = args[0]
    api_key = os.getenv("LMS_API_KEY", "YOUR_LMS_API_KEY")
    url = f"http://localhost:42002/analytics/pass-rates?lab={lab_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, timeout=10.0)
            if resp.status_code == 404:
                return f"Lab '{lab_id}' not found. Use /labs to see available labs."
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict) and "pass_rates" in data:
                rates = data["pass_rates"]
            elif isinstance(data, list):
                rates = data
            else:
                return f"No pass rate data found for {lab_id}"
            if not rates:
                return f"Lab '{lab_id}' not found. Use /labs to see available labs."
            lines = [f"Pass rates for {lab_id}:"]
            for item in rates:
                task = item.get("task", item.get("name", "Unknown task"))
                rate = item.get("rate", item.get("pass_rate", 0))
                attempts = item.get("attempts", 0)
                lines.append(f"- {task}: {rate:.1f}% ({attempts} attempts)")
            return "\n".join(lines)
    except httpx.ConnectError:
        return "Backend error: connection refused (localhost:42002). Check that the services are running."
    except httpx.HTTPStatusError as e:
        return f"Backend error: HTTP {e.response.status_code} {e.response.reason_phrase}. The backend service may be down."
    except Exception as e:
        return f"Backend error: {type(e).__name__}: {str(e)}"
