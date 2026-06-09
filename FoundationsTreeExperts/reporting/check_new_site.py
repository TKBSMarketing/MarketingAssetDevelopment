import os, sys, requests, json
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
TOKEN = os.getenv('META_ACCESS_TOKEN')
ACCOUNT_ID = os.getenv('META_AD_ACCOUNT_ID')
BASE = 'https://graph.facebook.com/v21.0'

print('=== ALL ACTIVITY SINCE MAY 12 (new site) ===')
r = requests.get(f'{BASE}/act_{ACCOUNT_ID}/insights', params={
    'access_token': TOKEN,
    'fields': 'campaign_name,objective,spend,impressions,clicks,actions,cost_per_action_type',
    'time_range': '{"since":"2026-05-12","until":"2026-05-15"}',
    'level': 'campaign',
    'limit': 20
})

for c in r.json().get('data', []):
    print(f"\n{c.get('campaign_name')} ({c.get('objective')})")
    print(f"  Spend: ${float(c.get('spend', 0)):.2f} | Impressions: {c.get('impressions')} | Clicks: {c.get('clicks')}")
    print(f"  ALL ACTIONS:")
    for a in sorted(c.get('actions', []), key=lambda x: x['action_type']):
        print(f"    {a['action_type']}: {a['value']}")

# Daily breakdown since May 12
print(f"\n\n=== DAILY BREAKDOWN SINCE MAY 12 ===")
r2 = requests.get(f'{BASE}/act_{ACCOUNT_ID}/insights', params={
    'access_token': TOKEN,
    'fields': 'spend,impressions,clicks,actions',
    'time_range': '{"since":"2026-05-12","until":"2026-05-15"}',
    'time_increment': 1,
    'limit': 20
})
for day in r2.json().get('data', []):
    actions = {a['action_type']: a['value'] for a in day.get('actions', [])}
    lc = actions.get('link_click', 0)
    lpv = actions.get('landing_page_view', 0)
    print(f"\n  {day.get('date_start')}:")
    print(f"    Spend: ${float(day.get('spend', 0)):.2f} | Clicks: {day.get('clicks')} | Link Clicks: {lc} | LPV: {lpv}")
    # Show any conversion-like events
    for k, v in sorted(actions.items()):
        if any(kw in k.lower() for kw in ['lead', 'call', 'custom', 'offsite', 'wizard', 'contact', 'submit', 'conversion']):
            print(f"    ** {k}: {v}")
