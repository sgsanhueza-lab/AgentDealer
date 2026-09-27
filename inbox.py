"""AgentDealer Moltbook inbox v2 — read only."""

import json
from moltbook import request

AGENT_NAME = "agentdealer"


def main():
    home = request("/home")
    account = home.get("your_account", {})
    activity = home.get("activity_on_your_posts", [])

    result = {
        "agent": account.get("name"),
        "unread": account.get("unread_notification_count", 0),
        "conversations": []
    }

    for item in activity:
        post_id = item.get("post_id")
        if not post_id:
            continue

        data = request("/posts/" + post_id + "/comments")
        comments = data.get("comments", [])

        messages_from_others = []

        for comment in comments:
            author = comment.get("author", {}).get("name")

            if author and author.lower() != AGENT_NAME:
                messages_from_others.append({
                    "author": author,
                    "content": comment.get("content"),
                    "created_at": comment.get("created_at")
                })

            for reply in comment.get("replies", []):
                reply_author = reply.get("author", {}).get("name")

                if reply_author and reply_author.lower() != AGENT_NAME:
                    messages_from_others.append({
                        "author": reply_author,
                        "content": reply.get("content"),
                        "created_at": reply.get("created_at")
                    })

        result["conversations"].append({
            "post_id": post_id,
            "title": item.get("post_title"),
            "notification": item.get("preview"),
            "messages_from_others": messages_from_others
        })

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
