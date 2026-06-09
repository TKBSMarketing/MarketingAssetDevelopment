import os, sys, requests, json
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
token = os.getenv('META_ACCESS_TOKEN')
account_id = os.getenv('META_AD_ACCOUNT_ID')

BASE = 'https://graph.facebook.com/v21.0'

# Pull campaigns
r = requests.get(f'{BASE}/act_{account_id}/campaigns', params={
    'access_token': token,
    'fields': 'name,status,objective,daily_budget,lifetime_budget,start_time',
    'limit': 25
})
campaigns = r.json().get('data', [])
print('=== CAMPAIGNS ===')
for c in campaigns:
    print(f"  {c['name']} | Status: {c['status']} | Objective: {c.get('objective', 'N/A')}")

# Pull last 7 days insights at campaign level
r2 = requests.get(f'{BASE}/act_{account_id}/insights', params={
    'access_token': token,
    'fields': 'campaign_name,spend,impressions,reach,clicks,ctr,cpc,actions',
    'date_preset': 'last_7d',
    'level': 'campaign',
    'limit': 25
})
insights = r2.json().get('data', [])
print('\n=== LAST 7 DAYS PERFORMANCE ===')
for row in insights:
    actions = row.get('actions', [])
    link_clicks = next((a['value'] for a in actions if a['action_type'] == 'link_click'), '0')
    name = row.get('campaign_name', 'Unknown')
    spend = float(row.get('spend', 0))
    impressions = row.get('impressions', 0)
    reach = row.get('reach', 0)
    clicks = row.get('clicks', 0)
    ctr = row.get('ctr', 0)
    cpc = float(row.get('cpc', 0))
    print(f"  {name}")
    print(f"    Spend: ${spend:.2f} | Impressions: {impressions} | Reach: {reach}")
    print(f"    Clicks: {clicks} | CTR: {ctr}% | CPC: ${cpc:.2f} | Link Clicks: {link_clicks}")

# Pull ad-level insights to see which creatives perform best
r3 = requests.get(f'{BASE}/act_{account_id}/insights', params={
    'access_token': token,
    'fields': 'ad_name,spend,impressions,clicks,ctr,cpc,actions',
    'date_preset': 'last_7d',
    'level': 'ad',
    'limit': 10,
    'sort': 'spend_descending'
})
ads = r3.json().get('data', [])
print('\n=== TOP ADS BY SPEND (Last 7 Days) ===')
for ad in ads:
    actions = ad.get('actions', [])
    link_clicks = next((a['value'] for a in actions if a['action_type'] == 'link_click'), '0')
    name = ad.get('ad_name', 'Unknown')
    spend = float(ad.get('spend', 0))
    clicks = ad.get('clicks', 0)
    ctr = ad.get('ctr', 0)
    cpc = float(ad.get('cpc', 0))
    print(f"  {name}")
    print(f"    Spend: ${spend:.2f} | Clicks: {clicks} | CTR: {ctr}% | CPC: ${cpc:.2f} | Link Clicks: {link_clicks}")
