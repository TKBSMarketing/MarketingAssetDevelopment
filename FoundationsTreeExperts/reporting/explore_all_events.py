import os, sys, requests, json
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
TOKEN = os.getenv('META_ACCESS_TOKEN')
ACCOUNT_ID = os.getenv('META_AD_ACCOUNT_ID')
BASE = 'https://graph.facebook.com/v21.0'

# Pull 90 days of data with ALL possible action breakdowns
print('=== ALL ACTION TYPES ACROSS ALL CAMPAIGNS (90 days) ===')
r = requests.get(f'{BASE}/act_{ACCOUNT_ID}/insights', params={
    'access_token': TOKEN,
    'fields': 'campaign_name,objective,actions,cost_per_action_type',
    'date_preset': 'last_90d',
    'level': 'campaign',
    'limit': 20
})

# Collect every unique action type
all_action_types = set()
for c in r.json().get('data', []):
    print(f"\n{'='*60}")
    print(f"  {c.get('campaign_name')} ({c.get('objective')})")
    for a in sorted(c.get('actions', []), key=lambda x: x['action_type']):
        all_action_types.add(a['action_type'])
        # Highlight anything that looks like a conversion/lead/call
        marker = ''
        at = a['action_type'].lower()
        if any(kw in at for kw in ['lead', 'call', 'custom', 'offsite', 'submit', 'contact', 'wizard', 'quote', 'conversion']):
            marker = ' <-- CONVERSION EVENT'
        print(f"    {a['action_type']}: {a['value']}{marker}")

    costs = c.get('cost_per_action_type', [])
    conversion_costs = [a for a in costs if any(kw in a['action_type'].lower() for kw in ['lead', 'call', 'custom', 'offsite', 'submit', 'contact', 'wizard', 'quote', 'conversion'])]
    if conversion_costs:
        print(f"\n  CONVERSION COSTS:")
        for a in conversion_costs:
            print(f"    {a['action_type']}: ${float(a['value']):.2f}")

print(f"\n\n{'='*60}")
print(f"ALL UNIQUE ACTION TYPES FOUND:")
for at in sorted(all_action_types):
    marker = ''
    if any(kw in at.lower() for kw in ['lead', 'call', 'custom', 'offsite', 'submit', 'contact', 'wizard', 'quote', 'conversion']):
        marker = ' <-- POTENTIAL CONVERSION'
    print(f"  {at}{marker}")

# Now try pulling with action_breakdowns to see sub-types of custom events
print(f"\n\n{'='*60}")
print('=== OFFSITE CONVERSION BREAKDOWN ===')
r2 = requests.get(f'{BASE}/act_{ACCOUNT_ID}/insights', params={
    'access_token': TOKEN,
    'fields': 'campaign_name,actions',
    'date_preset': 'last_90d',
    'level': 'campaign',
    'action_breakdowns': 'action_type',
    'limit': 20
})
for c in r2.json().get('data', []):
    offsite = [a for a in c.get('actions', []) if any(kw in a['action_type'].lower() for kw in ['offsite', 'lead', 'call', 'custom', 'submit', 'contact', 'wizard'])]
    if offsite:
        print(f"\n  {c.get('campaign_name')}:")
        for a in sorted(offsite, key=lambda x: x['action_type']):
            print(f"    {a['action_type']}: {a['value']}")
