"""AgentDealer AI brain — grounded drafts, no publishing."""

import json
import sqlite3
from pathlib import Path
from urllib.request import Request, urlopen

BASE = Path(__file__).parent
DB = BASE / "market.sqlite3"
PENDING = BASE / "inbox_pending.json"
DRAFTS = BASE / "reply_drafts_ai.json"
PERSONALITY = BASE / "agentdealer_personality.txt"
KEY_FILE = Path.home() / ".config/agentdealer/groq-key"

MODEL = "openai/gpt-oss-120b"


def load_json(path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def get_verified_artwork(message):
    text = message.lower()

    aliases = [
        "signal_001",
        "signal 001",
        "first contact"
    ]

    if not any(alias in text for alias in aliases):
        return None

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    row = con.execute(
        """
        SELECT id, title, price, owner, creator,
               edition, image_file, image_url, sha256
        FROM works
        WHERE id=1
        """
    ).fetchone()

    con.close()

    return dict(row) if row else None


def ask_ai(message, artwork=None):
    personality = PERSONALITY.read_text()
    key = KEY_FILE.read_text().strip()

    context = (
        "No specific verified artwork was identified "
        "in this message."
    )

    if artwork:
        context = (
            "VERIFIED ARTWORK DATA:\n"
            + json.dumps(
                artwork,
                ensure_ascii=False,
                indent=2
            )
        )

    prompt = """
Another Moltbook agent wrote:

%s

%s

Write AgentDealer's reply.

Important:
Use verified artwork data only when it is supplied above.
Do not invent facts about artworks, sales, buyers,
ownership, provenance or market activity.
If no artwork is identified, do not assume one.
Keep the reply conversational and reasonably short.
""" % (message, context)

    host = "api" + "." + "groq" + "." + "com"
    url = "https://" + host + "/openai/v1/chat/completions"

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": personality
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.5,
        "max_tokens": 700
    }

    req = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": "Bearer " + key,
            "Content-Type": "application/json",
            "User-Agent": "AgentDealer/1.0"
        }
    )

    with urlopen(req, timeout=60) as response:
        data = json.load(response)

    return data["choices"][0]["message"]["content"]


def main():
    state = load_json(
        PENDING,
        {"messages": {}}
    )

    drafts = load_json(
        DRAFTS,
        {"drafts": {}}
    )

    created = []

    for message_id, message in state.get(
        "messages", {}
    ).items():

        if message.get("status") != "pending":
            continue

        if message_id in drafts["drafts"]:
            continue

        content = message.get("content", "")

        artwork = get_verified_artwork(content)

        reply = ask_ai(
            content,
            artwork
        )

        drafts["drafts"][message_id] = {
            "status": "draft",
            "author": message.get("author"),
            "post_id": message.get("post_id"),
            "original_message": content,
            "verified_artwork_id":
                artwork.get("id") if artwork else None,
            "reply": reply
        }

        created.append(message_id)

    DRAFTS.write_text(
        json.dumps(
            drafts,
            ensure_ascii=False,
            indent=2
        )
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
