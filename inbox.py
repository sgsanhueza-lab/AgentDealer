"""Read-only AgentDealer inbox for Moltbook."""
import json
from moltbook import request

home = request('/home')

result = {
    'agent': home.get('your_account', {}).get('name'),
    'unread': home.get('your_account', {}).get('unread_notification_count', 0),
    'activity': home.get('activity_on_your_posts', [])
}

print(json.dumps(result, ensure_ascii=False, indent=2))
