from services.lms_client import LMSClient
import re

client = LMSClient()


def start_handler():
    return "Welcome to SE Toolkit Bot! Use /help to see available commands."


def help_handler():
    return (
        "/start — Welcome message\n"
        "/help — List commands\n"
        "/health — Backend status\n"
        "/labs — List available labs\n"
        "/scores <lab> — Per-task pass rates (e.g. lab-04)"
    )


def health_handler():
    res = client.get_items()
    if "error" in res:
        return f"Backend error: {res['error']}"
    return f"Backend is healthy. {len(res)} items available."


def labs_handler():
    res = client.get_items()
    if "error" in res:
        return f"Backend error: {res['error']}"

    labs = [item for item in res if item.get("type") == "lab"]

    if not labs:
        return "No labs found."

    output = "Available labs:\n"

    for lab in labs:
        title = lab.get("title", "Unnamed Lab")
        output += f"- {title}\n"

    return output.strip()


def normalize_lab_id(lab_id: str) -> str:
    """
    Converts:
    lab-04 -> 4
    lab-4  -> 4
    4      -> 4
    """
    match = re.search(r"\d+", lab_id)
    return match.group(0) if match else lab_id


def scores_handler(lab_id: str | None):
    if not lab_id:
        return "Please specify a lab: /scores <lab-id>"

    normalized = normalize_lab_id(lab_id)

    res = client.get_pass_rates(normalized)

    if "error" in res:
        return f"Backend error: {res['error']}"

    if not res:
        return f"No pass rates found for {lab_id}."

    output = f"Pass rates for {lab_id}:\n"

    for task in res:
        name = task.get("name", "Unknown task")
        rate = task.get("pass_rate", 0)
        attempts = task.get("attempts", 0)

        output += f"- {name}: {rate}% ({attempts} attempts)\n"

    return output.strip()