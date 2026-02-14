import logging

from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("microsoft_to_do")

mcp = FastMCP("microsoft_to_do")


def format_task_lists(data: dict) -> str:
    lists = data.get("value", [])
    if not lists:
        return "No task lists found."
    return "\n".join(f"- {tl['displayName']} (id: {tl['id']})" for tl in lists)


def format_tasks(data: dict, include_completed: bool = False) -> str:
    tasks = data.get("value", [])
    if not include_completed:
        tasks = [t for t in tasks if t.get("status") != "completed"]
    if not tasks:
        return "No tasks found."
    lines = []
    for t in tasks:
        due = ""
        if dt := t.get("dueDateTime"):
            due = f", due: {dt['dateTime'][:10]}"
        importance = t.get("importance", "normal")
        imp = f", importance: {importance}" if importance != "normal" else ""
        lines.append(f"- {t['title']} [{t['status']}{due}{imp}] (id: {t['id']})")
    return "\n".join(lines)


def format_task_detail(task: dict) -> str:
    lines = [f"# {task['title']}"]
    lines.append(f"Status: {task['status']}")
    lines.append(f"Importance: {task['importance']}")
    if dt := task.get("dueDateTime"):
        lines.append(f"Due: {dt['dateTime'][:10]}")
    lines.append(f"Reminder: {'on' if task.get('isReminderOn') else 'off'}")
    if cats := task.get("categories"):
        lines.append(f"Categories: {', '.join(cats)}")
    lines.append(f"Created: {task['createdDateTime']}")
    lines.append(f"Modified: {task['lastModifiedDateTime']}")
    if body := task.get("body", {}).get("content"):
        lines.append(f"\n{body}")
    checklist = task.get("_checklist_items", [])
    if checklist:
        lines.append("\nChecklist:")
        for item in checklist:
            check = "x" if item.get("isChecked") else " "
            lines.append(f"  [{check}] {item['displayName']}")
    return "\n".join(lines)
