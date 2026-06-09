import os, sys, requests, json
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
TOKEN = os.getenv('META_ACCESS_TOKEN')
ACCOUNT_ID = os.getenv('META_AD_ACCOUNT_ID')
BASE = 'https://graph.facebook.com/v21.0'

# Pull campaign insights with ALL action types visible
r = requests.get(f'{BASE}/act_{ACCOUNT_ID}/insights', params={
    'access_token': TOKEN,
    'fields': 'campaign_name,objective,spend,impressions,clicks,actions,cost_per_action_type',
    'date_preset': 'last_30d',
    'level': 'campaign',
    'limit': 10
})

for c in r.json().get('data', []):
    print(f"\n=== {c.get('campaign_name')} ({c.get('objective')}) ===")
    print(f"  Spend: ${float(c.get('spend', 0)):.2f}")

    print(f"\n  ALL ACTIONS:")
    for a in c.get('actions', []):
        print(f"    {a['action_type']}: {a['value']}")

    print(f"\n  COST PER ACTION:")
    for a in c.get('cost_per_action_type', []):
        print(f"    {a['action_type']}: ${float(a['value']):.2f}")
