import os, sys, requests, json
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
TOKEN = os.getenv('META_ACCESS_TOKEN')
ACCOUNT_ID = os.getenv('META_AD_ACCOUNT_ID')
BASE = 'https://graph.facebook.com/v21.0'
FILTER = '[{"field":"campaign.name","operator":"CONTAIN","value":"AstroPaws"}]'

# Try combining breakdowns to get the actual combo matrix
print('=== MULTI-BREAKDOWN: body + title + image ===')
r = requests.get(f'{BASE}/act_{ACCOUNT_ID}/insights', params={
    'access_token': TOKEN,
    'fields': 'spend,impressions,clicks,ctr,cpc,actions',
    'date_preset': 'last_7d',
    'breakdowns': 'body_asset,title_asset,image_asset',
    'filtering': FILTER,
    'limit': 20,
    'sort': 'spend_descending'
})
data = r.json()
if 'error' in data:
    print(f'ERROR: {data["error"].get("message")}')
else:
    rows = data.get('data', [])
    print(f'{len(rows)} combos returned')
    for row in rows[:10]:
        body = row.get('body_asset', {}).get('text', '?')[:40]
        title = row.get('title_asset', {}).get('text', '?')[:40]
        image = row.get('image_asset', {}).get('name', '?')
        spend = float(row.get('spend', 0))
        ctr = float(row.get('ctr', 0))
        cpc = float(row.get('cpc', 0))
        lc = 0
        for a in row.get('actions', []):
            if a['action_type'] == 'link_click':
                lc = int(a['value'])
        print(f'  ${spend:.2f} | CTR {ctr:.2f}% | CPC ${cpc:.2f} | LC {lc}')
        print(f'    Title: {title}')
        print(f'    Body:  {body}')
        print(f'    Image: {image}')
        print()
