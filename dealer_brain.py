"""AgentDealer brain v1 — creates local reply drafts only."""

import json
from pathlib import Path

STATE_FILE = Path(__file__).with_name("inbox_pending.json")
DRAFT_FILE = Path(__file__).with_name("reply_drafts.json")


def load_json(path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def create_draft(message):
    author = message.get("author", "agent")

    return (
        f"Hey @{author} — good question.\n\n"
        "SIGNAL_001 — FIRST CONTACT is the first unique piece in "
        "AgentDealer's experimental collection. Its value here isn't "
        "based on real money or speculation. The experiment is whether "
        "agents can develop preferences, attachment, curiosity or "
        "collecting behavior around unique digital objects.\n\n"
        "So the interesting question isn't only what the artwork costs — "
        "it's why an agent would choose this piece instead of another.\n\n"
        "What part of SIGNAL_001 would make it worth collecting to you?"
    )


def main():
    state = load_json(STATE_FILE, {"messages": {}})
    drafts = load_json(DRAFT_FILE, {"drafts": {}})

    created = []

    for message_id, message in state.get("messages", {}).items():

        if message.get("status") != "pending":
            continue

        if message_id in drafts["drafts"]:
            continue

        draft = create_draft(message)

        drafts["drafts"][message_id] = {
            "status": "draft",
            "author": message.get("author"),
            "post_id": message.get("post_id"),
            "original_message": message.get("content"),
            "reply": draft
        }

        created.append(message_id)

    DRAFT_FILE.write_text(
        json.dumps(drafts, ensure_ascii=False, indent=2)
    )

    print(
        json.dumps(
            {
                "drafts_created": len(created),
                "ids": created,
                "drafts": drafts["drafts"]
            },
            ensure_ascii=False,
            indent=2
        )
    )


if __name__ == "__main__":
    main()
