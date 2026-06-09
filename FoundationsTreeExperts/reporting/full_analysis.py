import os, sys, requests, json
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
TOKEN = os.getenv('META_ACCESS_TOKEN')
ACCOUNT_ID = os.getenv('META_AD_ACCOUNT_ID')
BASE = 'https://graph.facebook.com/v21.0'

def get(endpoint, params):
    params['access_token'] = TOKEN
    return requests.get(f'{BASE}/{endpoint}', params=params).json()

# Campaign level
camps = get(f'act_{ACCOUNT_ID}/insights', {
    'fields': 'campaign_name,objective,spend,impressions,reach,clicks,ctr,cpc,actions,cost_per_action_type',
    'date_preset': 'last_90d', 'level': 'campaign', 'limit': 20
}).get('data', [])

print('='*80)
print('CAMPAIGN PERFORMANCE (90 days)')
print('='*80)
for c in camps:
    actions = {a['action_type']: int(a['value']) for a in c.get('actions', [])}
    costs = {a['action_type']: float(a['value']) for a in c.get('cost_per_action_type', [])}
    spend = float(c.get('spend', 0))
    lc = actions.get('link_click', 0)
    lpv = actions.get('landing_page_view', 0)
    leads = actions.get('lead', 0) or actions.get('offsite_conversion.fb_pixel_lead', 0)
    vv = actions.get('video_view', 0)
    eng = actions.get('post_engagement', 0)
    print(f"\n{c['campaign_name']} ({c.get('objective', 'N/A')})")
    print(f"  Spend: ${spend:.2f} | Impressions: {c.get('impressions')} | Reach: {c.get('reach')}")
    print(f"  CTR: {float(c.get('ctr',0)):.2f}% | CPC (all): ${float(c.get('cpc',0)):.2f}")
    print(f"  Link Clicks: {lc} | CPC (link): ${spend/lc:.2f}" if lc else f"  Link Clicks: 0")
    print(f"  Landing Page Views: {lpv} | Cost/LPV: ${spend/lpv:.2f}" if lpv else f"  LPV: 0")
    print(f"  Leads: {leads} | Cost/Lead: ${spend/leads:.2f}" if leads else f"  Leads: 0")
    print(f"  Video Views: {vv} | Cost/View: ${spend/vv:.4f}" if vv else f"  Video Views: 0")
    print(f"  Post Engagements: {eng} | Cost/Eng: ${spend/eng:.4f}" if eng else f"  Engagements: 0")

# Ad level
print('\n' + '='*80)
print('AD PERFORMANCE (90 days)')
print('='*80)
ads = get(f'act_{ACCOUNT_ID}/insights', {
    'fields': 'ad_name,campaign_name,adset_name,spend,impressions,clicks,ctr,actions',
    'date_preset': 'last_90d', 'level': 'ad', 'limit': 30, 'sort': 'spend_descending'
}).get('data', [])

for a in ads:
    actions = {act['action_type']: int(act['value']) for act in a.get('actions', [])}
    spend = float(a.get('spend', 0))
    lc = actions.get('link_click', 0)
    lpv = actions.get('landing_page_view', 0)
    leads = actions.get('lead', 0) or actions.get('offsite_conversion.fb_pixel_lead', 0) or actions.get('offsite_conversion.fb_pixel_custom', 0)
    vv = actions.get('video_view', 0)
    print(f"\n{a['ad_name']} | {a.get('campaign_name', '')}")
    print(f"  Ad Set: {a.get('adset_name', '')}")
    print(f"  Spend: ${spend:.2f} | CTR: {float(a.get('ctr',0)):.2f}%")
    print(f"  Link Clicks: {lc}" + (f" | CPC(link): ${spend/lc:.2f}" if lc else ""))
    print(f"  LPV: {lpv}" + (f" | Cost/LPV: ${spend/lpv:.2f}" if lpv else ""))
    print(f"  Leads: {leads}" + (f" | Cost/Lead: ${spend/leads:.2f}" if leads else ""))
    print(f"  Video Views: {vv}")

# Image breakdown
print('\n' + '='*80)
print('IMAGE CREATIVE PERFORMANCE (90 days)')
print('='*80)
for camp in camps:
    camp_id = camp.get('campaign_id', '')
    if not camp_id:
        continue
    try:
        imgs = get(f'act_{ACCOUNT_ID}/insights', {
            'fields': 'ad_name,spend,impressions,clicks,ctr,actions',
            'date_preset': 'last_90d', 'breakdowns': 'image_asset',
            'filtering': f'[{{"field":"campaign.id","operator":"EQUAL","value":"{camp_id}"}}]',
            'limit': 20, 'sort': 'spend_descending'
        }).get('data', [])
        if imgs:
            print(f"\n--- {camp['campaign_name']} ---")
            for img in imgs:
                asset = img.get('image_asset', {})
                actions = {act['action_type']: int(act['value']) for act in img.get('actions', [])}
                spend = float(img.get('spend', 0))
                lc = actions.get('link_click', 0)
                print(f"  {asset.get('name', 'N/A')[:50]}")
                print(f"    Spend: ${spend:.2f} | CTR: {float(img.get('ctr',0)):.2f}% | LC: {lc}" + (f" | CPC(link): ${spend/lc:.2f}" if lc else ""))
    except:
        pass

# Age/gender
print('\n' + '='*80)
print('AGE/GENDER PERFORMANCE (90 days)')
print('='*80)
demo = get(f'act_{ACCOUNT_ID}/insights', {
    'fields': 'spend,impressions,clicks,ctr,cpc,actions',
    'date_preset': 'last_90d', 'breakdowns': 'age,gender', 'limit': 50
}).get('data', [])

for row in sorted(demo, key=lambda x: float(x.get('spend',0)), reverse=True):
    if row.get('gender', 'unknown').lower() == 'unknown':
        continue
    actions = {a['action_type']: int(a['value']) for a in row.get('actions', [])}
    spend = float(row.get('spend', 0))
    lc = actions.get('link_click', 0)
    leads = actions.get('lead', 0)
    print(f"  {row.get('gender','?').title()} {row.get('age','?')}: ${spend:.2f} spend | CTR: {float(row.get('ctr',0)):.2f}% | LC: {lc}" + (f" | CPC(link): ${spend/lc:.2f}" if lc else "") + (f" | Leads: {leads}" if leads else ""))

# Platform
print('\n' + '='*80)
print('PLATFORM/PLACEMENT (90 days)')
print('='*80)
plat = get(f'act_{ACCOUNT_ID}/insights', {
    'fields': 'spend,impressions,clicks,ctr,actions',
    'date_preset': 'last_90d', 'breakdowns': 'publisher_platform,platform_position',
    'limit': 30, 'sort': 'spend_descending'
}).get('data', [])

for row in plat:
    actions = {a['action_type']: int(a['value']) for a in row.get('actions', [])}
    spend = float(row.get('spend', 0))
    lc = actions.get('link_click', 0)
    platform = row.get('publisher_platform', '?')
    position = row.get('platform_position', '?')
    print(f"  {platform} / {position}: ${spend:.2f} | CTR: {float(row.get('ctr',0)):.2f}% | LC: {lc}" + (f" | CPC(link): ${spend/lc:.2f}" if lc else ""))
