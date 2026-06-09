import os, sys, requests, json
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
TOKEN = os.getenv('META_ACCESS_TOKEN')
ACCOUNT_ID = os.getenv('META_AD_ACCOUNT_ID')
BASE = 'https://graph.facebook.com/v21.0'
FILTER = '[{"field":"campaign.name","operator":"CONTAIN","value":"AstroPaws"}]'

# Try body + title pair
print('=== BODY + TITLE BREAKDOWN ===')
r = requests.get(f'{BASE}/act_{ACCOUNT_ID}/insights', params={
    'access_token': TOKEN,
    'fields': 'spend,impressions,clicks,ctr,cpc,actions',
    'date_preset': 'last_7d',
    'breakdowns': 'body_asset,title_asset',
    'filtering': FILTER,
    'limit': 10,
    'sort': 'spend_descending'
})
data = r.json()
if 'error' in data:
    print(f'ERROR: {data["error"].get("message")}')
else:
    print(f'{len(data.get("data", []))} rows')
    for row in data.get('data', [])[:5]:
        body = row.get('body_asset', {}).get('text', '?')[:50]
        title = row.get('title_asset', {}).get('text', '?')[:50]
        spend = float(row.get('spend', 0))
        ctr = float(row.get('ctr', 0))
        cpc = float(row.get('cpc', 0))
        print(f'  ${spend:.2f} | CTR {ctr:.2f}% | CPC ${cpc:.2f}')
        print(f'    Headline: {title}')
        print(f'    Primary:  {body}')
        print()

# Pull ad-level data with creative fields
print('\n=== AD CREATIVES WITH BODY + TITLE ===')
r2 = requests.get(f'{BASE}/act_{ACCOUNT_ID}/ads', params={
    'access_token': TOKEN,
    'fields': 'name,creative{title,body,thumbnail_url,image_url}',
    'filtering': FILTER,
    'limit': 20
})
data2 = r2.json()
if 'error' in data2:
    print(f'ERROR: {data2["error"].get("message")}')
else:
    print(json.dumps(data2, indent=2, default=str)[:3000])

# Pull ad-level insights with ad_id to join
print('\n=== AD-LEVEL INSIGHTS WITH ENGAGEMENT ===')
r3 = requests.get(f'{BASE}/act_{ACCOUNT_ID}/insights', params={
    'access_token': TOKEN,
    'fields': 'ad_id,ad_name,spend,impressions,clicks,ctr,cpc,actions',
    'date_preset': 'last_7d',
    'level': 'ad',
    'filtering': FILTER,
    'limit': 20,
    'sort': 'spend_descending'
})
for row in r3.json().get('data', []):
    lc = 0
    lpv = 0
    for a in row.get('actions', []):
        if a['action_type'] == 'link_click': lc = int(a['value'])
        if a['action_type'] == 'landing_page_view': lpv = int(a['value'])
    print(f"  {row['ad_name']} (ID: {row['ad_id']})")
    print(f"    Spend: ${float(row['spend']):.2f} | CTR: {float(row['ctr']):.2f}% | CPC: ${float(row['cpc']):.2f} | LC: {lc} | LPV: {lpv}")
