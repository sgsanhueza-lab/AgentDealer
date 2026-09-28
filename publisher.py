"""AgentDealer publisher — explicit human approval required."""

import argparse
import json
from pathlib import Path

DRAFTS = Path(__file__).with_name("reply_drafts_ai.json")


def load_drafts():
    if not DRAFTS.exists():
        return {"drafts": {}}

    return json.loads(DRAFTS.read_text())


def save_drafts(data):
    DRAFTS.write_text(
        json.dumps(data, ensure_ascii=False, indent=2)
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("message_id")
    parser.add_argument(
        "--approve",
        action="store_true"
    )
    parser.add_argument(
        "--confirm-publish",
        action="store_true"
    )

    args = parser.parse_args()
    data = load_drafts()

    draft = data.get(
        "drafts", {}
    ).get(args.message_id)

    if not draft:
        raise SystemExit("Draft not found.")

    print("\n--- DRAFT ---\n")
    print(draft.get("reply", ""))
    print("\n-------------\n")

    if args.approve:
        draft["status"] = "approved"
        save_drafts(data)
        print("Draft approved locally.")
        return

    if args.confirm_publish:
        if draft.get("status") != "approved":
            raise SystemExit(
                "REFUSED: draft is not approved."
            )

        post_id = draft.get("post_id", "")

        if not post_id or post_id.startswith("LOCAL-"):
            raise SystemExit(
                "REFUSED: invalid or local test post."
            )

        from moltbook import request

        result = request(
            "/posts/" + post_id + "/comments",
            "POST",
            {
                "content": draft["reply"]
            }
        )

        draft["status"] = "published"
        draft["moltbook_result"] = result

        save_drafts(data)

        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2
            )
        )

        return

    print(
        "READ ONLY: use --approve to approve locally. "
        "Publishing requires a separate "
        "--confirm-publish command."
    )


if __name__ == "__main__":
    main()
