import httpx, os
async def handle_labs(args=None):
    k=os.getenv("LMS_API_KEY","something")
    try:
        async with httpx.AsyncClient() as c:
            r=await c.get("http://localhost:42002/items/",headers={"Authorization":f"Bearer {k}"},timeout=10)
            r.raise_for_status()
            d=r.json()
            labs=[i for i in d if i.get("type")=="lab"]
            lines=["Available labs:"]
            for L in labs: lines.append(f"- {L.get('title',L.get('name','Untitled'))}")
            return "\n".join(lines)
    except httpx.ConnectError: return "Backend error: connection refused (localhost:42002). Check that the services are running."
    except httpx.HTTPStatusError as e: return f"Backend error: HTTP {e.response.status_code} {e.response.reason_phrase}. The backend service may be down."
    except Exception as e: return f"Backend error: {type(e).__name__}: {str(e)}"
