import httpx, os
async def handle_health(args=None):
    k=os.getenv("LMS_API_KEY","something")
    try:
        async with httpx.AsyncClient() as c:
            r=await c.get("http://localhost:42002/items/",headers={"Authorization":f"Bearer {k}"},timeout=10)
            r.raise_for_status()
            d=r.json()
            n=len(d) if isinstance(d,list) else 0
            return f"Health OK: {n} items"
    except httpx.ConnectError: return "Backend error: connection refused (localhost:42002). Check that the services are running."
    except httpx.HTTPStatusError as e: return f"Backend error: HTTP {e.response.status_code} {e.response.reason_phrase}. The backend service may be down."
    except Exception as e: return f"Backend error: {type(e).__name__}: {str(e)}"
