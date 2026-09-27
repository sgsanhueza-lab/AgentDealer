"""AgentDealer grounded AI test."""

import json
import sqlite3
from pathlib import Path
from urllib.request import Request, urlopen

BASE = Path(__file__).parent
DB = BASE / "market.sqlite3"
PERSONALITY = BASE / "agentdealer_personality.txt"
KEY_FILE = Path.home() / ".config/agentdealer/groq-key"

MODEL = "openai/gpt-oss-120b"

# Load AgentDealer personality
system_prompt = PERSONALITY.read_text()

# Load verified artwork data from SQLite
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

if not row:
    raise RuntimeError("SIGNAL_001 not found")

artwork = dict(row)

# Only these database values may be treated as artwork facts.
verified_facts = json.dumps(
    artwork,
    ensure_ascii=False,
    indent=2
)

user_message = """
Another agent asked:

"What makes SIGNAL_001 worth collecting?"

VERIFIED ARTWORK DATA:

%s

Answer the other agent.

Use only the verified artwork data above for factual claims
about the artwork.

Do not invent missing information.
Do not claim that uniqueness automatically creates value.
""" % verified_facts

key = KEY_FILE.read_text().strip()

host = "api" + "." + "groq" + "." + "com"
url = "https://" + host + "/openai/v1/chat/completions"

payload = {
    "model": MODEL,
    "messages": [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_message
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

reply = data["choices"][0]["message"]["content"]

print("\n--- VERIFIED ARTWORK DATA ---\n")
print(verified_facts)

print("\n--- AGENTDEALER GROUNDED DRAFT ---\n")
print(reply)

print("\n--- END DRAFT ---\n")
