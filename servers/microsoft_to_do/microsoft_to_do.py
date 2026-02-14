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
