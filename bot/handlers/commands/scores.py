import httpx, os
async def handle_scores(args=None):
    if not args or len(args)==0: return "Usage: /scores <lab-id>. Example: /scores lab-04"
    lid=args[0]; k=os.getenv("LMS_API_KEY","something")
    try:
        async with httpx.AsyncClient() as c:
            r=await c.get(f"http://localhost:42002/analytics/pass-rates?lab={lid}",headers={"Authorization":f"Bearer {k}"},timeout=10)
            if r.status_code==404: return "Lab not found. Use /labs to see available labs."
            r.raise_for_status()
            d=r.json()
            rates=d.get("pass_rates",d) if isinstance(d,dict) else d
            if not rates: return "Lab not found. Use /labs to see available labs."
            ln=lid.replace("lab-","")
            lines=[f"Pass rates for Lab {ln}:"]
            for it in rates:
                t=it.get("task",it.get("name","Unknown"))
                rt=it.get("rate",it.get("pass_rate",0))
                at=it.get("attempts",0)
                lines.append(f"- {t}: {rt:.1f}% ({at} attempts)")
            return "\n".join(lines)
    except httpx.ConnectError: return "Backend error: connection refused (localhost:42002). Check that the services are running."
    except httpx.HTTPStatusError as e: return f"Backend error: HTTP {e.response.status_code} {e.response.reason_phrase}. The backend service may be down."
    except Exception as e: return f"Backend error: {type(e).__name__}: {str(e)}"
