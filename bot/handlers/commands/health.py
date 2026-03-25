from services.lms_client import LMSClient

client = LMSClient()

def health_handler():
    res = client.get_items()
    if "error" in res:
        return f"Backend error: {res['error']}"
    return f"Health OK: {len(res)} items"
