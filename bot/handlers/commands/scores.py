from services.lms_client import LMSClient

client = LMSClient()

def scores_handler(lab_id: str | None):
    if not lab_id:
        return "Please specify a lab: /scores <lab-id>"

    lab_id_norm = lab_id.lower().replace(" ", "")
    res = client.get_pass_rates(lab_id_norm)
    if "error" in res:
        return f"Backend error: {res['error']}"
    if not res:
        return f"No pass rates found for {lab_id}."

    output = f"Pass rates for {lab_id}:\n"
    for task in res:
        name = task.get("task") or task.get("title") or "Unknown task"
        rate = round(task.get("avg_score", 0), 1)
        attempts = task.get("attempts", 0)
        output += f"- {name}: {rate}% ({attempts} attempts)\n"

    return output.strip()
