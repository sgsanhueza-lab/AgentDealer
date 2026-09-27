"""AgentDealer inbox v4 — pending-message workflow."""

import json
from pathlib import Path
from moltbook import request

AGENT_NAME = "agentdealer"
STATE_FILE = Path(__file__).with_name("inbox_pending.json")


def load_state():
    if not STATE_FILE.exists():
        return {"messages": {}}

    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {"messages": {}}


def save_state(state):
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2)
    )


def inspect_message(item, post_id, post_title, state):
    author = item.get("author", {}).get("name")
    message_id = item.get("id")

    if not author or not message_id:
        return

    if author.lower() == AGENT_NAME:
        return

    if message_id not in state["messages"]:
        state["messages"][message_id] = {
            "status": "pending",
            "author": author,
            "content": item.get("content"),
            "post_id": post_id,
            "post_title": post_title,
            "created_at": item.get("created_at")
        }


def main():
    state = load_state()
    home = request("/home")

    for activity in home.get("activity_on_your_posts", []):
        post_id = activity.get("post_id")
        post_title = activity.get("post_title")

        if not post_id:
            continue

        data = request("/posts/" + post_id + "/comments")

        for comment in data.get("comments", []):
            inspect_message(
                comment,
                post_id,
                post_title,
                state
            )

            for reply in comment.get("replies", []):
                inspect_message(
                    reply,
                    post_id,
                    post_title,
                    state
                )

    save_state(state)

    pending = []

    for message_id, message in state["messages"].items():
        if message.get("status") == "pending":
            pending.append({
                "id": message_id,
                **message
            })

    result = {
        "agent": home.get(
            "your_account", {}
        ).get("name"),
        "pending_count": len(pending),
        "pending_messages": pending
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
