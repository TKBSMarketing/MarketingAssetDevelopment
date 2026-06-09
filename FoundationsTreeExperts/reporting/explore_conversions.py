import os, sys, requests, json
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
TOKEN = os.getenv('META_ACCESS_TOKEN')
ACCOUNT_ID = os.getenv('META_AD_ACCOUNT_ID')
BASE = 'https://graph.facebook.com/v21.0'

# Pull ALL action types including offsite conversions
r = requests.get(f'{BASE}/act_{ACCOUNT_ID}/insights', params={
    'access_token': TOKEN,
    'fields': 'campaign_name,objective,spend,actions,action_values,cost_per_action_type',
    'date_preset': 'last_30d',
    'level': 'campaign',
    'limit': 10
})

for c in r.json().get('data', []):
    print(f"\n{'='*60}")
    print(f"  {c.get('campaign_name')} ({c.get('objective')})")
    print(f"  Spend: ${float(c.get('spend', 0)):.2f}")

    print(f"\n  ALL ACTIONS:")
    for a in sorted(c.get('actions', []), key=lambda x: x['action_type']):
        print(f"    {a['action_type']}: {a['value']}")

    print(f"\n  COST PER ACTION:")
    for a in sorted(c.get('cost_per_action_type', []), key=lambda x: x['action_type']):
        print(f"    {a['action_type']}: ${float(a['value']):.2f}")

    if c.get('action_values'):
        print(f"\n  ACTION VALUES:")
        for a in c.get('action_values', []):
            print(f"    {a['action_type']}: ${float(a['value']):.2f}")

# Also try with the specific conversion action types
print(f"\n\n{'='*60}")
print("=== CHECKING FOR CUSTOM CONVERSIONS ===")
r2 = requests.get(f'{BASE}/act_{ACCOUNT_ID}/insights', params={
    'access_token': TOKEN,
    'fields': 'campaign_name,actions,cost_per_action_type',
    'date_preset': 'last_90d',
    'level': 'campaign',
    'limit': 10,
    'action_breakdowns': 'action_type'
})
for c in r2.json().get('data', []):
    offsite = [a for a in c.get('actions', []) if 'offsite' in a['action_type'] or 'lead' in a['action_type'].lower()]
    if offsite:
        print(f"\n  {c.get('campaign_name')}:")
        for a in offsite:
            print(f"    {a['action_type']}: {a['value']}")
        costs = [a for a in c.get('cost_per_action_type', []) if 'offsite' in a['action_type'] or 'lead' in a['action_type'].lower()]
        for a in costs:
            print(f"    COST: {a['action_type']}: ${float(a['value']):.2f}")
