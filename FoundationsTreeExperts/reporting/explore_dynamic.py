import os, sys, requests, json
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
TOKEN = os.getenv('META_ACCESS_TOKEN')
ACCOUNT_ID = os.getenv('META_AD_ACCOUNT_ID')
BASE = 'https://graph.facebook.com/v21.0'

# The "Images" ad uses dynamic creative with 6 images
# Let's try image_asset breakdown filtered to just that ad or its campaign
AD_ID = '120245816151490351'  # "Images" ad

# Try 1: image_asset breakdown filtered to the specific campaign
print('=== IMAGE ASSET BREAKDOWN - FTE/Leads campaign only ===')
r = requests.get(f'{BASE}/act_{ACCOUNT_ID}/insights', params={
    'access_token': TOKEN,
    'fields': 'ad_name,spend,impressions,clicks,ctr,actions',
    'date_preset': 'last_30d',
    'level': 'ad',
    'breakdowns': 'image_asset',
    'filtering': '[{"field":"campaign.name","operator":"CONTAIN","value":"FTE"}]',
    'limit': 20,
    'sort': 'spend_descending'
})
data = r.json()
if 'error' in data:
    print(f'ERROR: {data["error"]["message"]}')
else:
    rows = data.get('data', [])
    print(f'{len(rows)} rows')
    for row in rows:
        asset = row.get('image_asset', {})
        lc = 0
        for a in row.get('actions', []):
            if a['action_type'] == 'link_click':
                lc = int(a['value'])
        print(f"  {row.get('ad_name', '?')}")
        print(f"    Image: {asset.get('name', 'N/A')} | Hash: {asset.get('hash', 'N/A')[:20]}")
        print(f"    Spend: ${float(row.get('spend', 0)):.2f} | Clicks: {row.get('clicks', 0)} | LC: {lc} | CTR: {float(row.get('ctr', 0)):.2f}%")
        print(f"    URL: {asset.get('url', 'N/A')[:120]}")
        print()

# Try 2: Get the ad's asset_feed_spec to see all images
print('\n=== ASSET FEED SPEC for Images ad ===')
r2 = requests.get(f'{BASE}/{AD_ID}', params={
    'access_token': TOKEN,
    'fields': 'name,creative{asset_feed_spec,thumbnail_url}'
})
data2 = r2.json()
creative = data2.get('creative', {})
afs = creative.get('asset_feed_spec', {})
images = afs.get('images', [])
print(f'{len(images)} images in asset feed')
for i, img in enumerate(images):
    hash_val = img.get('hash', 'N/A')
    # Try to get image URL from hash
    print(f'  Image {i+1}: hash={hash_val}')

# Try 3: Use the image hashes to get URLs
print('\n=== RESOLVE IMAGE HASHES TO URLs ===')
for img in images:
    hash_val = img.get('hash', '')
    if hash_val:
        r3 = requests.get(f'{BASE}/act_{ACCOUNT_ID}/adimages', params={
            'access_token': TOKEN,
            'hashes': json.dumps([hash_val]),
        })
        img_data = r3.json().get('data', {})
        if hash_val in img_data:
            url = img_data[hash_val].get('url', 'N/A')
            name = img_data[hash_val].get('name', 'N/A')
            print(f'  {name} | {url[:120]}')
        else:
            print(f'  Hash {hash_val[:20]} not found')
