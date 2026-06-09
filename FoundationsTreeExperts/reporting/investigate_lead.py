import os, sys, requests, json
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
TOKEN = os.getenv('META_ACCESS_TOKEN')
ACCOUNT_ID = os.getenv('META_AD_ACCOUNT_ID')
BASE = 'https://graph.facebook.com/v21.0'

CAMPAIGN_ID = None

# First find the campaign ID
camps = requests.get(f'{BASE}/act_{ACCOUNT_ID}/campaigns', params={
    'access_token': TOKEN,
    'fields': 'id,name',
    'filtering': '[{"field":"name","operator":"CONTAIN","value":"FTE"}]',
    'limit': 10
}).json().get('data', [])

for c in camps:
    print(f"  {c['id']} | {c['name']}")
    if 'Lookalike' in c['name']:
        CAMPAIGN_ID = c['id']

print(f"\nInvestigating campaign: {CAMPAIGN_ID}")

# Pull insights with ALL action types and date breakdown
print('\n=== DAILY BREAKDOWN WITH ALL ACTIONS ===')
r = requests.get(f'{BASE}/act_{ACCOUNT_ID}/insights', params={
    'access_token': TOKEN,
    'fields': 'spend,impressions,clicks,actions,cost_per_action_type',
    'filtering': f'[{{"field":"campaign.id","operator":"EQUAL","value":"{CAMPAIGN_ID}"}}]',
    'time_increment': 1,
    'date_preset': 'last_90d',
    'limit': 100
})
for day in r.json().get('data', []):
    actions = day.get('actions', [])
    offsite = [a for a in actions if 'offsite' in a['action_type'] or 'lead' in a['action_type'].lower() or 'custom' in a['action_type']]
    if offsite:
        print(f"\n  Date: {day.get('date_start')}")
        print(f"  Spend: ${float(day.get('spend', 0)):.2f} | Clicks: {day.get('clicks')}")
        for a in offsite:
            print(f"    {a['action_type']}: {a['value']}")
        for a in day.get('cost_per_action_type', []):
            if 'offsite' in a['action_type'] or 'lead' in a['action_type'].lower() or 'custom' in a['action_type']:
                print(f"    COST: {a['action_type']}: ${float(a['value']):.2f}")

# Pull at ad level too
print('\n=== AD LEVEL - ALL ACTIONS ===')
r2 = requests.get(f'{BASE}/act_{ACCOUNT_ID}/insights', params={
    'access_token': TOKEN,
    'fields': 'ad_name,ad_id,spend,actions,cost_per_action_type',
    'filtering': f'[{{"field":"campaign.id","operator":"EQUAL","value":"{CAMPAIGN_ID}"}}]',
    'date_preset': 'last_90d',
    'level': 'ad',
    'limit': 20
})
for ad in r2.json().get('data', []):
    print(f"\n  {ad.get('ad_name')} (ID: {ad.get('ad_id')})")
    print(f"  Spend: ${float(ad.get('spend', 0)):.2f}")
    print(f"  ALL ACTIONS:")
    for a in sorted(ad.get('actions', []), key=lambda x: x['action_type']):
        print(f"    {a['action_type']}: {a['value']}")

# Check what the custom conversion event actually is
print('\n=== CUSTOM CONVERSIONS ON THIS ACCOUNT ===')
r3 = requests.get(f'{BASE}/act_{ACCOUNT_ID}/customconversions', params={
    'access_token': TOKEN,
    'fields': 'id,name,description,pixel,rule,default_conversion_value',
    'limit': 20
})
data3 = r3.json()
if 'error' in data3:
    print(f"  Error: {data3['error'].get('message')}")
else:
    for cc in data3.get('data', []):
        print(f"  {cc.get('name')} (ID: {cc.get('id')})")
        print(f"    Rule: {cc.get('rule')}")
        print(f"    Description: {cc.get('description', 'N/A')}")
