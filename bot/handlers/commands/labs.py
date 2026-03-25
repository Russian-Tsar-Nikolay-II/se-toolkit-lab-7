from services.lms_client import LMSClient

client = LMSClient()

def labs_handler():
    res = client.get_items()
    if "error" in res:
        return f"Backend error: {res['error']}"

    labs = [item for item in res if item.get("type") == "lab"]
    if not labs:
        return "No labs found."

    output = "Available labs:\n"
    for lab in labs:
        lab_id = lab.get("id", "")
        title = lab.get("title", "Unnamed Lab")
        output += f"- Lab {lab_id} — {title}\n"

    return output.strip()
