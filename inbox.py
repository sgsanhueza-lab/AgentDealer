"""AgentDealer Moltbook inbox v3 — read only with local memory."""

import json
from pathlib import Path
from moltbook import request

AGENT_NAME = "agentdealer"
STATE_FILE = Path(__file__).with_name("inbox_state.json")


def load_seen():
    if not STATE_FILE.exists():
        return set()

    try:
        data = json.loads(STATE_FILE.read_text())
        return set(data.get("seen", []))
    except Exception:
        return set()


def save_seen(seen):
    STATE_FILE.write_text(
        json.dumps(
            {"seen": sorted(seen)},
            ensure_ascii=False,
            indent=2
        )
    )


def collect_message(comment):
    author = comment.get("author", {}).get("name")

    if not author or author.lower() == AGENT_NAME:
        return None

    return {
        "id": comment.get("id"),
        "author": author,
        "content": comment.get("content"),
        "created_at": comment.get("created_at")
    }


def main():
    seen = load_seen()
    home = request("/home")

    account = home.get("your_account", {})
    activity = home.get("activity_on_your_posts", [])

    new_messages = []
    all_seen = set(seen)

    for item in activity:
        post_id = item.get("post_id")

        if not post_id:
            continue

        data = request("/posts/" + post_id + "/comments")
        comments = data.get("comments", [])

        for comment in comments:
            message = collect_message(comment)

            if message and message["id"]:
                all_seen.add(message["id"])

                if message["id"] not in seen:
                    message["post_id"] = post_id
                    message["post_title"] = item.get("post_title")
                    new_messages.append(message)

            for reply in comment.get("replies", []):
                message = collect_message(reply)

                if message and message["id"]:
                    all_seen.add(message["id"])

                    if message["id"] not in seen:
                        message["post_id"] = post_id
                        message["post_title"] = item.get("post_title")
                        new_messages.append(message)

    save_seen(all_seen)

    result = {
        "agent": account.get("name"),
        "moltbook_unread": account.get(
            "unread_notification_count", 0
        ),
        "new_messages_from_other_agents": len(new_messages),
        "messages": new_messages
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
