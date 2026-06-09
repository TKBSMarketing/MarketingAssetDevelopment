import os, sys, requests, json
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
TOKEN = os.getenv('META_ACCESS_TOKEN')
ACCOUNT_ID = os.getenv('META_AD_ACCOUNT_ID')
BASE = 'https://graph.facebook.com/v21.0'
FILTER = '[{"field":"campaign.name","operator":"CONTAIN","value":"AstroPaws"}]'

for breakdown_name in ['body_asset', 'title_asset', 'description_asset']:
    print(f'\n=== {breakdown_name.upper()} BREAKDOWN ===')
    r = requests.get(f'{BASE}/act_{ACCOUNT_ID}/insights', params={
        'access_token': TOKEN,
        'fields': 'ad_name,spend,impressions,clicks,ctr,cpc,actions',
        'date_preset': 'last_7d',
        'breakdowns': breakdown_name,
        'filtering': FILTER,
        'limit': 50,
        'sort': 'spend_descending'
    })
    data = r.json()
    if 'error' in data:
        print(f'  ERROR: {data["error"].get("message", "Unknown")}')
    else:
        rows = data.get('data', [])
        print(f'  {len(rows)} rows returned')
        print(json.dumps(rows[:5], indent=2, default=str))

# Also try pulling ad creatives with full text fields
print('\n=== AD CREATIVES WITH TEXT ===')
r2 = requests.get(f'{BASE}/act_{ACCOUNT_ID}/ads', params={
    'access_token': TOKEN,
    'fields': 'name,creative{title,body,link_description,asset_feed_spec,object_story_spec}',
    'filtering': FILTER,
    'limit': 50
})
print(json.dumps(r2.json(), indent=2, default=str))
