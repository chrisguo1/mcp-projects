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
