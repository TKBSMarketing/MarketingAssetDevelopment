import os, sys, requests, json
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
TOKEN = os.getenv('META_ACCESS_TOKEN')
ACCOUNT_ID = os.getenv('META_AD_ACCOUNT_ID')
BASE = 'https://graph.facebook.com/v21.0'

# Get ad-level insights with ad_id
print('=== AD-LEVEL INSIGHTS ===')
r = requests.get(f'{BASE}/act_{ACCOUNT_ID}/insights', params={
    'access_token': TOKEN,
    'fields': 'ad_id,ad_name,adset_name,campaign_name,spend,impressions,clicks,ctr,actions',
    'date_preset': 'last_30d',
    'level': 'ad',
    'limit': 20,
    'sort': 'spend_descending'
})
ads = r.json().get('data', [])
ad_ids = []
for ad in ads[:10]:
    ad_ids.append(ad['ad_id'])
    lc = 0
    for a in ad.get('actions', []):
        if a['action_type'] == 'link_click':
            lc = int(a['value'])
    print(f"  {ad['ad_name']} (ID: {ad['ad_id']})")
    print(f"    Campaign: {ad.get('campaign_name', 'N/A')} | Ad Set: {ad.get('adset_name', 'N/A')}")
    print(f"    Spend: ${float(ad['spend']):.2f} | Clicks: {ad['clicks']} | Link Clicks: {lc}")

# For each ad, get its creative with image/video
print('\n=== AD CREATIVE DETAILS ===')
for ad_id in ad_ids[:10]:
    r2 = requests.get(f'{BASE}/{ad_id}', params={
        'access_token': TOKEN,
        'fields': 'name,creative{thumbnail_url,image_url,image_hash,video_id,object_story_spec,asset_feed_spec}'
    })
    data = r2.json()
    creative = data.get('creative', {})
    print(f"\n  Ad: {data.get('name', 'Unknown')} (ID: {ad_id})")
    print(f"    Thumbnail: {creative.get('thumbnail_url', 'None')[:80]}")
    print(f"    Image URL: {creative.get('image_url', 'None')[:80]}")
    print(f"    Image Hash: {creative.get('image_hash', 'None')}")
    print(f"    Video ID: {creative.get('video_id', 'None')}")

    # Check asset_feed_spec for dynamic creative images
    afs = creative.get('asset_feed_spec', {})
    if afs:
        images = afs.get('images', [])
        videos = afs.get('videos', [])
        print(f"    Asset Feed: {len(images)} images, {len(videos)} videos")
        for img in images[:5]:
            print(f"      Image hash: {img.get('hash', 'N/A')} | URL: {img.get('url', 'N/A')[:80]}")
        for vid in videos[:5]:
            print(f"      Video ID: {vid.get('video_id', 'N/A')} | Thumbnail: {vid.get('thumbnail_url', 'N/A')[:80]}")

# Also try image_asset breakdown with ad_name to see per-ad image performance
print('\n=== IMAGE ASSET BREAKDOWN (with ad_name) ===')
r3 = requests.get(f'{BASE}/act_{ACCOUNT_ID}/insights', params={
    'access_token': TOKEN,
    'fields': 'ad_name,adset_name,campaign_name,spend,impressions,clicks,ctr,actions',
    'date_preset': 'last_30d',
    'breakdowns': 'image_asset',
    'limit': 30,
    'sort': 'spend_descending'
})
data3 = r3.json().get('data', [])
print(f'{len(data3)} rows')
for row in data3[:15]:
    asset = row.get('image_asset', {})
    lc = 0
    for a in row.get('actions', []):
        if a['action_type'] == 'link_click':
            lc = int(a['value'])
    print(f"  {row.get('ad_name', '?')} | {row.get('adset_name', '?')}")
    print(f"    Image: {asset.get('name', 'N/A')} | Hash: {asset.get('hash', 'N/A')[:20]}")
    print(f"    Spend: ${float(row.get('spend', 0)):.2f} | Clicks: {row.get('clicks', 0)} | Link Clicks: {lc} | CTR: {float(row.get('ctr', 0)):.2f}%")
    print(f"    URL: {asset.get('url', 'N/A')[:100]}")
    print()
