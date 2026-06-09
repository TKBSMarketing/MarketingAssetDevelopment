import os, sys, requests, json
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
TOKEN = os.getenv('META_ACCESS_TOKEN')
ACCOUNT_ID = os.getenv('META_AD_ACCOUNT_ID')
BASE = 'https://graph.facebook.com/v21.0'

# Pull ads with creative details
r = requests.get(f'{BASE}/act_{ACCOUNT_ID}/ads', params={
    'access_token': TOKEN,
    'fields': 'name,status,creative{title,body,image_url,thumbnail_url,object_story_spec}',
    'filtering': '[{"field":"campaign.name","operator":"CONTAIN","value":"AstroPaws"}]',
    'limit': 50
})
ads = r.json()
print('=== ADS WITH CREATIVE DETAILS ===')
print(json.dumps(ads, indent=2, default=str))

# Pull ad-level insights with creative breakdowns
r2 = requests.get(f'{BASE}/act_{ACCOUNT_ID}/insights', params={
    'access_token': TOKEN,
    'fields': 'ad_name,ad_id,spend,impressions,clicks,ctr,cpc,actions',
    'date_preset': 'last_7d',
    'level': 'ad',
    'filtering': '[{"field":"campaign.name","operator":"CONTAIN","value":"AstroPaws"}]',
    'limit': 50,
    'sort': 'spend_descending'
})
print('\n=== AD-LEVEL INSIGHTS ===')
print(json.dumps(r2.json(), indent=2, default=str))

# Try breakdowns by image/video asset
r3 = requests.get(f'{BASE}/act_{ACCOUNT_ID}/insights', params={
    'access_token': TOKEN,
    'fields': 'ad_name,spend,impressions,clicks,ctr,cpc,actions',
    'date_preset': 'last_7d',
    'level': 'ad',
    'breakdowns': 'image_asset',
    'filtering': '[{"field":"campaign.name","operator":"CONTAIN","value":"AstroPaws"}]',
    'limit': 50
})
print('\n=== IMAGE ASSET BREAKDOWN ===')
print(json.dumps(r3.json(), indent=2, default=str))

# Try age/gender breakdown for audience insights
r4 = requests.get(f'{BASE}/act_{ACCOUNT_ID}/insights', params={
    'access_token': TOKEN,
    'fields': 'spend,impressions,clicks,ctr,cpc,actions',
    'date_preset': 'last_7d',
    'breakdowns': 'age,gender',
    'filtering': '[{"field":"campaign.name","operator":"CONTAIN","value":"AstroPaws"}]',
    'limit': 50
})
print('\n=== AGE/GENDER BREAKDOWN ===')
print(json.dumps(r4.json(), indent=2, default=str))

# Try platform/placement breakdown
r5 = requests.get(f'{BASE}/act_{ACCOUNT_ID}/insights', params={
    'access_token': TOKEN,
    'fields': 'spend,impressions,clicks,ctr,cpc,actions',
    'date_preset': 'last_7d',
    'breakdowns': 'publisher_platform,platform_position',
    'filtering': '[{"field":"campaign.name","operator":"CONTAIN","value":"AstroPaws"}]',
    'limit': 50
})
print('\n=== PLATFORM/PLACEMENT BREAKDOWN ===')
print(json.dumps(r5.json(), indent=2, default=str))
