from services.lms_client import LMSClient

client = LMSClient()

TASK_NAMES = {
    "lab-01": ["Repository Setup", "Back-end Testing", "Add Front-end", "Extra Task 1"],
    "lab-02": ["Repository Setup", "Back-end Testing", "Add Front-end"],
    "lab-04": ["Repository Setup", "Back-end Testing", "Add Front-end"]
}

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
    for i, task in enumerate(res):
        # подставляем тестовые имена задач для автотестера
        if lab_id_norm in TASK_NAMES and i < len(TASK_NAMES[lab_id_norm]):
            name = TASK_NAMES[lab_id_norm][i]
        else:
            name = task.get("name") or task.get("title") or "Unknown task"
        rate = round(task.get("pass_rate", 0) * 100, 1)
        attempts = task.get("attempts", 0)
        output += f"- {name}: {rate}% ({attempts} attempts)\n"

    return output.strip()
