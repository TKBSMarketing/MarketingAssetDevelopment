"""
Build the TKBS/FTE/Leads/Lookalike/10%Off/CL campaign from scratch.
Mirrors the Dyn campaign structure with the D-series 10% discount images.
"""
import os, sys, json, requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
TOKEN = os.getenv('META_ACCESS_TOKEN')
ACCOUNT_ID = os.getenv('META_AD_ACCOUNT_ID')
BASE = 'https://graph.facebook.com/v21.0'
ACT = f'act_{ACCOUNT_ID}'

PAGE_ID = '459924217499119'
INSTAGRAM_ID = '17841460052316684'
PIXEL_ID = '1673544533983863'

CAMPAIGN_NAME = 'TKBS/FTE/Leads/Lookalike/10%Off/CL'

IMAGES = [
    os.path.join(os.path.dirname(__file__), '..', 'ads', 'D1-save-10-percent.png'),
    os.path.join(os.path.dirname(__file__), '..', 'ads', 'D2-10-off-tree-removal.png'),
    os.path.join(os.path.dirname(__file__), '..', 'ads', 'D3-dont-wait-save-10.png'),
    os.path.join(os.path.dirname(__file__), '..', 'ads', 'D4-10-off-cleanup-included.png'),
]

BODIES = [
    "You know which tree we're talking about.\n\nThe one you've been meaning to deal with since last year. The one you think about every time it storms. The one you keep telling yourself you'll handle \"soon.\"\n\nIt's not getting smaller. And it's not getting safer.\n\nOne call. A real person answers. We walk your yard, give you an honest assessment, and put a written quote in your hands. No games, no pressure.\n\nFoundations Tree Experts — 26 Years of Service",
    "Every storm, you check the window.\n\nThe dead limb over the bedroom. The trunk that leans a little more each year. The roots pushing up through the driveway.\n\nWhat if the next storm was just... a storm? No anxiety. No 2 AM window checks. Just rain on the roof and you, sleeping.\n\nThat's what we do. We remove the worry.\n\nFoundations Tree Experts — Ann Arbor · ISA Arborist on Staff · Fully Insured",
    "That tree is not a weekend project.\n\nEvery year, homeowners end up in the ER trying to save a few hundred bucks. Falling branches, chainsaw kickback, ladder accidents — it's not worth the risk.\n\nOur crew does this every day. Licensed. Insured. ISA Certified. And when we're done, we clean up everything — not just the tree.\n\nGet a free estimate today.",
]

TITLES = [
    "Ann Arbor's Trusted Tree Experts",
    "Don't Wait Until It Falls",
    "Free Estimate — No Obligation",
]

DESCRIPTIONS = [
    "Tree Removal · Trimming · Stump Grinding",
    "Licensed & Insured · Free Estimates",
]

URL_TAGS = "utm_source=Facebook&utm_medium={{placement}}&utm_campaign={{campaign.name}}&utm_term={{adset.name}}&utm_content={{ad.name}}&campaign_id={{campaign.id}}"


def api_post(endpoint, data=None, files=None):
    if data is None:
        data = {}
    data['access_token'] = TOKEN
    r = requests.post(f'{BASE}/{endpoint}', data=data, files=files)
    if r.status_code >= 400:
        print(f'ERROR {r.status_code}: {r.text}')
    r.raise_for_status()
    return r.json()


def step(label):
    print(f'\n{"="*60}\n  {label}\n{"="*60}')


def main():
    # ── 1. Create Campaign ──
    step('1. Creating Campaign')
    campaign = api_post(f'{ACT}/campaigns', {
        'name': CAMPAIGN_NAME,
        'objective': 'OUTCOME_LEADS',
        'status': 'PAUSED',
        'bid_strategy': 'LOWEST_COST_WITHOUT_CAP',
        'daily_budget': '1000',
        'special_ad_categories': '[]',
    })
    campaign_id = campaign['id']
    print(f'  Campaign created: {campaign_id}')

    # ── 2. Create Ad Set ──
    step('2. Creating Ad Set')
    targeting = json.dumps({
        "age_max": 65,
        "age_min": 25,
        "excluded_geo_locations": {
            "cities": [{
                "country": "US",
                "distance_unit": "mile",
                "key": "2467497",
                "name": "Detroit",
                "radius": 15,
                "region": "Michigan",
                "region_id": "3865"
            }],
            "location_types": ["home", "recent"]
        },
        "flexible_spec": [{
            "interests": [
                {"id": "6003053056644", "name": "Gardening"},
                {"id": "6003195091098", "name": "Landscaping"},
                {"id": "6003234413249", "name": "Home improvement"},
                {"id": "6005060777126", "name": "Backyard"}
            ]
        }],
        "geo_locations": {
            "cities": [{
                "country": "US",
                "distance_unit": "mile",
                "key": "2466923",
                "name": "Ann Arbor",
                "radius": 20,
                "region": "Michigan",
                "region_id": "3865"
            }],
            "location_types": ["home", "recent"]
        },
        "targeting_automation": {
            "advantage_audience": 1,
            "individual_setting": {
                "age": 1,
                "gender": 1,
                "geo": 0
            }
        }
    })

    adset = api_post(f'{ACT}/adsets', {
        'name': 'Lookalike FTE 10% Off',
        'campaign_id': campaign_id,
        'status': 'PAUSED',
        'targeting': targeting,
        'billing_event': 'IMPRESSIONS',
        'optimization_goal': 'OFFSITE_CONVERSIONS',
        'promoted_object': json.dumps({
            "pixel_id": PIXEL_ID,
            "custom_event_type": "LEAD"
        }),
        'destination_type': 'UNDEFINED',
    })
    adset_id = adset['id']
    print(f'  Ad Set created: {adset_id}')

    # ── 3. Upload Images ──
    step('3. Uploading Images')
    image_hashes = []
    for img_path in IMAGES:
        abs_path = os.path.abspath(img_path)
        filename = os.path.basename(abs_path)
        print(f'  Uploading {filename}...')
        with open(abs_path, 'rb') as f:
            result = api_post(f'{ACT}/adimages', files={'filename': (filename, f, 'image/png')})
        img_data = result.get('images', {})
        hash_val = list(img_data.values())[0]['hash']
        image_hashes.append(hash_val)
        print(f'    Hash: {hash_val}')

    print(f'\n  All {len(image_hashes)} images uploaded successfully')

    # ── 4. Create Ad Creative ──
    step('4. Creating Ad Creative')
    asset_feed_spec = json.dumps({
        "images": [{"hash": h} for h in image_hashes],
        "bodies": [{"text": t} for t in BODIES],
        "titles": [{"text": t} for t in TITLES],
        "descriptions": [{"text": t} for t in DESCRIPTIONS],
        "link_urls": [{"website_url": "https://www.foundationstreeexperts.com/"}],
        "call_to_action_types": ["GET_QUOTE"],
        "ad_formats": ["AUTOMATIC_FORMAT"],
        "optimization_type": "REGULAR",
    })

    object_story_spec = json.dumps({
        "page_id": PAGE_ID,
        "instagram_user_id": INSTAGRAM_ID,
    })

    creative = api_post(f'{ACT}/adcreatives', {
        'name': f'{CAMPAIGN_NAME} — Dynamic Creative',
        'object_story_spec': object_story_spec,
        'asset_feed_spec': asset_feed_spec,
        'url_tags': URL_TAGS,
    })
    creative_id = creative['id']
    print(f'  Creative created: {creative_id}')

    # ── 5. Create Ad ──
    step('5. Creating Ad')
    ad = api_post(f'{ACT}/ads', {
        'name': '10% Off Images',
        'adset_id': adset_id,
        'creative': json.dumps({'creative_id': creative_id}),
        'status': 'PAUSED',
    })
    ad_id = ad['id']
    print(f'  Ad created: {ad_id}')

    # ── Summary ──
    step('BUILD COMPLETE')
    print(f'''
  Campaign:  {CAMPAIGN_NAME}
  Campaign ID: {campaign_id}
  Ad Set ID:   {adset_id}
  Creative ID: {creative_id}
  Ad ID:       {ad_id}
  Status:      PAUSED (ready for review)

  Images:      {len(image_hashes)} uploaded (D1-D4 discount series)
  Bodies:      {len(BODIES)} copy variants
  Titles:      {len(TITLES)} headline variants
  Descriptions:{len(DESCRIPTIONS)} description variants

  Next: Review in Ads Manager, then publish when ready.
''')


if __name__ == '__main__':
    main()
