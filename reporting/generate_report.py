"""
AstroPaws Ad Performance Report Generator
Pulls data from Meta Marketing API and generates a client-ready PDF report.

Usage: python generate_report.py [--days 7] [--output report.pdf]
"""
import os, sys, argparse, requests, re
from datetime import datetime, timedelta
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, Image as RLImage
)
import tempfile
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.graphics.shapes import Drawing, PolyLine, Rect
from reportlab.graphics import renderPDF

sys.stdout.reconfigure(encoding='utf-8')

# Shared metric helpers (extractors, formatters, objective config, traffic light).
# Imported with * so the insight engine and PDF builder can use them by bare name.
import metrics as M
from metrics import *  # noqa: F401,F403
from profiles import select_profile, profile_for_objective

USABLE_WIDTH = 7.3 * inch  # letter width 8.5 - 0.6in left - 0.6in right

BRAND_CHARCOAL = HexColor('#1B2838')
BRAND_MINT = HexColor('#00D4AA')
BRAND_LIGHT = HexColor('#f5f5f5')
BRAND_GRAY = HexColor('#666666')
BRAND_DARK = HexColor('#222222')
WHITE = HexColor('#ffffff')
BEST_ROW = HexColor('#e6f9f0')
WORST_ROW = HexColor('#fde8e8')

BASE = 'https://graph.facebook.com/v21.0'

# Client config is populated by configure_client() once --client is resolved.
# This single script serves every client; each client supplies only a .env.
TOKEN = None
ACCOUNT_ID = None
CAMPAIGN_FILTER = ''
CLIENT_NAME = 'Ad Performance'
FILTER_PARAM = '[]'


def configure_client(client_dir):
    """Load a client's .env and populate the module-level Meta config."""
    global TOKEN, ACCOUNT_ID, CAMPAIGN_FILTER, CLIENT_NAME, FILTER_PARAM
    load_dotenv(os.path.join(client_dir, '.env'), override=True)
    TOKEN = os.getenv('META_ACCESS_TOKEN')
    ACCOUNT_ID = os.getenv('META_AD_ACCOUNT_ID')
    CAMPAIGN_FILTER = os.getenv('CAMPAIGN_FILTER', '').strip()
    CLIENT_NAME = os.getenv('CLIENT_NAME', 'Ad Performance')
    FILTER_PARAM = (
        f'[{{"field":"campaign.name","operator":"CONTAIN","value":"{CAMPAIGN_FILTER}"}}]'
        if CAMPAIGN_FILTER else '[]'
    )


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def api_get(endpoint, params):
    params['access_token'] = TOKEN
    r = requests.get(f'{BASE}/{endpoint}', params=params)
    r.raise_for_status()
    return r.json()


def fetch_account_info():
    return api_get(f'act_{ACCOUNT_ID}', {
        'fields': 'name,currency,timezone_name'
    })


def fetch_campaign_insights(date_preset='last_7d'):
    data = api_get(f'act_{ACCOUNT_ID}/insights', {
        'fields': 'campaign_name,campaign_id,objective,spend,impressions,reach,clicks,ctr,cpc,cpp,actions,action_values,cost_per_action_type',
        'date_preset': date_preset,
        'level': 'campaign',
        'filtering': FILTER_PARAM,
        'limit': 50
    })
    return data.get('data', [])


def fetch_adset_insights(date_preset='last_7d'):
    data = api_get(f'act_{ACCOUNT_ID}/insights', {
        'fields': 'adset_name,spend,impressions,reach,clicks,ctr,cpc,actions',
        'date_preset': date_preset,
        'level': 'adset',
        'filtering': FILTER_PARAM,
        'limit': 50,
        'sort': 'spend_descending'
    })
    return data.get('data', [])


def fetch_ad_insights(date_preset='last_7d'):
    data = api_get(f'act_{ACCOUNT_ID}/insights', {
        'fields': 'ad_id,ad_name,adset_name,campaign_name,spend,impressions,clicks,ctr,cpc,actions',
        'date_preset': date_preset,
        'level': 'ad',
        'filtering': FILTER_PARAM,
        'limit': 20,
        'sort': 'spend_descending'
    })
    return data.get('data', [])


def fetch_ad_thumbnails(ad_ids):
    """Fetch thumbnail URLs for a list of ad IDs. Returns dict of ad_id -> thumbnail_url."""
    thumbnails = {}
    for ad_id in ad_ids:
        try:
            data = api_get(ad_id, {'fields': 'creative{thumbnail_url}'})
            thumb = data.get('creative', {}).get('thumbnail_url', '')
            if thumb:
                thumbnails[ad_id] = thumb
        except Exception:
            pass
    return thumbnails


def fetch_daily_insights(days=7):
    today = datetime.now()
    since = (today - timedelta(days=days)).strftime('%Y-%m-%d')
    until = today.strftime('%Y-%m-%d')
    data = api_get(f'act_{ACCOUNT_ID}/insights', {
        'fields': 'spend,impressions,reach,clicks,ctr,cpc,actions,action_values',
        'time_range': f'{{"since":"{since}","until":"{until}"}}',
        'time_increment': 1,
        'filtering': FILTER_PARAM,
        'limit': 100
    })
    return data.get('data', [])


def fetch_image_breakdown(date_preset='last_7d'):
    """Fetch image asset breakdown. If global filter returns nothing, try per-campaign."""
    data = api_get(f'act_{ACCOUNT_ID}/insights', {
        'fields': 'ad_name,spend,impressions,clicks,ctr,cpc,actions',
        'date_preset': date_preset,
        'breakdowns': 'image_asset',
        'filtering': FILTER_PARAM,
        'limit': 100,
        'sort': 'spend_descending'
    })
    results = data.get('data', [])
    if results:
        return results

    # Fallback: try per-campaign (some campaigns use dynamic creative, others don't)
    try:
        campaigns = api_get(f'act_{ACCOUNT_ID}/campaigns', {
            'fields': 'id,name',
            'filtering': FILTER_PARAM,
            'limit': 50
        }).get('data', [])
        all_results = []
        for camp in campaigns:
            camp_filter = f'[{{"field":"campaign.id","operator":"EQUAL","value":"{camp["id"]}"}}]'
            try:
                camp_data = api_get(f'act_{ACCOUNT_ID}/insights', {
                    'fields': 'ad_name,spend,impressions,clicks,ctr,cpc,actions',
                    'date_preset': date_preset,
                    'breakdowns': 'image_asset',
                    'filtering': camp_filter,
                    'limit': 50,
                    'sort': 'spend_descending'
                })
                all_results.extend(camp_data.get('data', []))
            except Exception:
                pass
        return sorted(all_results, key=lambda x: float(x.get('spend', 0)), reverse=True)
    except Exception:
        return []


def fetch_age_gender_breakdown(date_preset='last_7d'):
    data = api_get(f'act_{ACCOUNT_ID}/insights', {
        'fields': 'spend,impressions,clicks,ctr,cpc,actions',
        'date_preset': date_preset,
        'breakdowns': 'age,gender',
        'filtering': FILTER_PARAM,
        'limit': 100
    })
    return data.get('data', [])


def fetch_platform_breakdown(date_preset='last_7d'):
    data = api_get(f'act_{ACCOUNT_ID}/insights', {
        'fields': 'spend,impressions,clicks,ctr,cpc,actions',
        'date_preset': date_preset,
        'breakdowns': 'publisher_platform,platform_position',
        'filtering': FILTER_PARAM,
        'limit': 100
    })
    return data.get('data', [])


def fetch_body_breakdown(date_preset='last_7d'):
    data = api_get(f'act_{ACCOUNT_ID}/insights', {
        'fields': 'ad_name,spend,impressions,clicks,ctr,cpc,actions',
        'date_preset': date_preset,
        'breakdowns': 'body_asset',
        'filtering': FILTER_PARAM,
        'limit': 50,
        'sort': 'spend_descending'
    })
    return data.get('data', [])


def fetch_title_breakdown(date_preset='last_7d'):
    data = api_get(f'act_{ACCOUNT_ID}/insights', {
        'fields': 'ad_name,spend,impressions,clicks,ctr,cpc,actions',
        'date_preset': date_preset,
        'breakdowns': 'title_asset',
        'filtering': FILTER_PARAM,
        'limit': 50,
        'sort': 'spend_descending'
    })
    return data.get('data', [])


def fetch_description_breakdown(date_preset='last_7d'):
    data = api_get(f'act_{ACCOUNT_ID}/insights', {
        'fields': 'ad_name,spend,impressions,clicks,ctr,cpc,actions',
        'date_preset': date_preset,
        'breakdowns': 'description_asset',
        'filtering': FILTER_PARAM,
        'limit': 50,
        'sort': 'spend_descending'
    })
    return data.get('data', [])


def fetch_ad_creative_details(ad_id):
    """Fetch creative details (title, body, thumbnail) for a specific ad."""
    data = api_get(f'{ad_id}', {
        'fields': 'name,creative{title,body,thumbnail_url}'
    })
    return data


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

# Metric extractors, formatters, objective config, and the traffic-light helpers
# now live in metrics.py (imported with * above). Only the reportlab-bound
# drawing/IO helpers remain here.


def make_sparkline(values, width=120, height=25, color=None):
    """Create a small sparkline Drawing from a list of numeric values."""
    if color is None:
        color = BRAND_MINT
    if not values or len(values) < 2:
        return None
    d = Drawing(width, height)
    min_v = min(values)
    max_v = max(values)
    rng = max_v - min_v if max_v != min_v else 1
    points = []
    for i, v in enumerate(values):
        x = (i / (len(values) - 1)) * (width - 4) + 2
        y = ((v - min_v) / rng) * (height - 6) + 3
        points.extend([x, y])
    d.add(PolyLine(points, strokeColor=color, strokeWidth=1.5))
    return d


def download_thumbnail(url, max_size=(90, 90)):
    """Download an image URL and return a reportlab Image flowable, or None on failure."""
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        tmp = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        tmp.write(r.content)
        tmp.close()
        from PIL import Image as PILImage
        img = PILImage.open(tmp.name)
        w, h = img.size
        aspect = w / h
        disp_h = max_size[1]
        disp_w = disp_h * aspect
        if disp_w > max_size[0]:
            disp_w = max_size[0]
            disp_h = disp_w / aspect
        return RLImage(tmp.name, width=disp_w, height=disp_h)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Insight engine
# ---------------------------------------------------------------------------

def generate_insights(campaigns, image_data, age_gender_data, platform_data,
                      total_spend, total_link_clicks, avg_ctr, avg_cpc,
                      body_data=None, title_data=None, desc_data=None):
    """Generate actionable insights from all data breakdowns."""
    insights = []

    # --- Creative insights ---
    if image_data:
        images_with_metrics = []
        for row in image_data:
            img_name = clean_image_name(row.get('image_asset', {}).get('name', row.get('ad_name', 'Unknown')))
            ctr = float(row.get('ctr', 0))
            cpc = calc_link_cpc(row)
            spend = float(row.get('spend', 0))
            lc = extract_link_clicks(row)
            if spend > 0:
                images_with_metrics.append({
                    'name': img_name, 'ctr': ctr, 'cpc': cpc,
                    'spend': spend, 'link_clicks': lc
                })

        if len(images_with_metrics) >= 2:
            best_ctr_img = max(images_with_metrics, key=lambda x: x['ctr'])
            worst_ctr_img = min(images_with_metrics, key=lambda x: x['ctr'])
            best_cpc_img = min(images_with_metrics, key=lambda x: x['cpc'] if x['cpc'] > 0 else 999)

            insights.append(
                f'<b>Top creative by CTR:</b> "{best_ctr_img["name"]}" at '
                f'{fmt_pct(best_ctr_img["ctr"])} CTR and {fmt_money(best_ctr_img["cpc"])} CPC (Link).'
            )

            if worst_ctr_img['name'] != best_ctr_img['name']:
                insights.append(
                    f'<b>Lowest CTR creative:</b> "{worst_ctr_img["name"]}" at '
                    f'{fmt_pct(worst_ctr_img["ctr"])} CTR. Consider pausing or replacing this image.'
                )

            if best_ctr_img['ctr'] > 0 and worst_ctr_img['ctr'] > 0:
                ctr_advantage = (best_ctr_img['ctr'] - worst_ctr_img['ctr']) / worst_ctr_img['ctr']
                if ctr_advantage > 0.20:
                    insights.append(
                        f'<b>Creative opportunity:</b> "{best_ctr_img["name"]}" has '
                        f'{ctr_advantage:.0%} higher CTR than the weakest image. '
                        f'Recommend shifting more budget to this creative.'
                    )

            if best_cpc_img['name'] != best_ctr_img['name']:
                insights.append(
                    f'<b>Most efficient creative:</b> "{best_cpc_img["name"]}" drives '
                    f'the cheapest link clicks at {fmt_money(best_cpc_img["cpc"])} CPC (Link).'
                )

    # --- Audience insights ---
    if age_gender_data:
        age_groups = {}
        gender_segments = {}
        for row in age_gender_data:
            age = row.get('age', 'Unknown')
            gender = row.get('gender', 'unknown')
            if gender.lower() == 'unknown':
                continue
            spend = float(row.get('spend', 0))
            impressions = int(row.get('impressions', 0))
            clicks = int(row.get('clicks', 0))
            lc = extract_link_clicks(row)

            if age not in age_groups:
                age_groups[age] = {'spend': 0, 'impressions': 0, 'clicks': 0, 'link_clicks': 0}
            age_groups[age]['spend'] += spend
            age_groups[age]['impressions'] += impressions
            age_groups[age]['clicks'] += clicks
            age_groups[age]['link_clicks'] += lc

            segment_key = f'{gender.title()} {age}'
            if segment_key not in gender_segments:
                gender_segments[segment_key] = {'spend': 0, 'impressions': 0, 'clicks': 0, 'link_clicks': 0}
            gender_segments[segment_key]['spend'] += spend
            gender_segments[segment_key]['impressions'] += impressions
            gender_segments[segment_key]['clicks'] += clicks
            gender_segments[segment_key]['link_clicks'] += lc

        # Best age group by CPC (Link)
        age_with_lc = {k: v for k, v in age_groups.items() if v['link_clicks'] > 0}
        if age_with_lc:
            best_age_cpc = min(age_with_lc.items(), key=lambda x: x[1]['spend'] / x[1]['link_clicks'])
            age_cpc = best_age_cpc[1]['spend'] / best_age_cpc[1]['link_clicks']
            age_ctr = best_age_cpc[1]['clicks'] / best_age_cpc[1]['impressions'] * 100 if best_age_cpc[1]['impressions'] else 0
            insights.append(
                f'<b>Best age group:</b> {best_age_cpc[0]} has the lowest CPC (Link) at '
                f'{fmt_money(age_cpc)} with {fmt_pct(age_ctr)} CTR.'
            )

        # Best gender segment
        gender_with_lc = {k: v for k, v in gender_segments.items() if v['link_clicks'] > 0}
        if gender_with_lc:
            best_segment = min(gender_with_lc.items(), key=lambda x: x[1]['spend'] / x[1]['link_clicks'])
            seg_cpc = best_segment[1]['spend'] / best_segment[1]['link_clicks']
            insights.append(
                f'<b>Top audience segment:</b> {best_segment[0]} at '
                f'{fmt_money(seg_cpc)} CPC (Link) with {fmt_number(best_segment[1]["link_clicks"])} link clicks.'
            )

        # Underperforming segments
        for seg_name, seg in gender_segments.items():
            if seg['impressions'] > 0 and seg['spend'] > 0.50:
                seg_ctr = seg['clicks'] / seg['impressions'] * 100
                seg_cpc = seg['spend'] / seg['link_clicks'] if seg['link_clicks'] > 0 else 999
                if seg_ctr < 1.0 or seg_cpc > 0.50:
                    reason = []
                    if seg_ctr < 1.0:
                        reason.append(f'CTR only {fmt_pct(seg_ctr)}')
                    if seg_cpc > 0.50:
                        reason.append(f'CPC (Link) at {fmt_money(seg_cpc)}')
                    insights.append(
                        f'<b>Underperforming segment:</b> {seg_name} -- {", ".join(reason)}. '
                        f'Consider reducing spend or excluding this segment.'
                    )
                    break  # Only report the worst one to avoid clutter

    # --- Platform insights ---
    if platform_data:
        placements = []
        for row in platform_data:
            spend = float(row.get('spend', 0))
            if spend < 0.50:
                continue
            platform = row.get('publisher_platform', '')
            position = row.get('platform_position', '')
            name = clean_placement_name(platform, position)
            lc = extract_link_clicks(row)
            clicks = int(row.get('clicks', 0))
            impressions = int(row.get('impressions', 0))
            cpc = spend / lc if lc > 0 else 999
            ctr = clicks / impressions * 100 if impressions > 0 else 0
            placements.append({
                'name': name, 'spend': spend, 'link_clicks': lc,
                'clicks': clicks, 'cpc': cpc, 'ctr': ctr
            })

        if placements:
            placements_with_lc = [p for p in placements if p['link_clicks'] > 0]
            if placements_with_lc:
                best_placement = min(placements_with_lc, key=lambda x: x['spend'] / x['link_clicks'])
                cost_per_lc = best_placement['spend'] / best_placement['link_clicks']
                insights.append(
                    f'<b>Best placement for link clicks:</b> {best_placement["name"]} -- '
                    f'{fmt_number(best_placement["link_clicks"])} link clicks at '
                    f'{fmt_money(cost_per_lc)} per click.'
                )

            # Placements burning budget with no link clicks
            zero_click_placements = [p for p in placements if p['link_clicks'] == 0 and p['spend'] > 1.00]
            if zero_click_placements:
                names = ', '.join(p['name'] for p in zero_click_placements[:3])
                total_wasted = sum(p['spend'] for p in zero_click_placements)
                insights.append(
                    f'<b>Budget waste alert:</b> {names} spent {fmt_money(total_wasted)} '
                    f'with zero link clicks. Consider excluding these placements.'
                )

    # --- Headline insights ---
    if title_data:
        titles_with_metrics = []
        for row in title_data:
            text = truncate_text(row.get('title_asset', {}).get('text', row.get('ad_name', 'Unknown')), 50)
            spend = float(row.get('spend', 0))
            ctr = float(row.get('ctr', 0))
            if spend > 1.0:
                titles_with_metrics.append({'text': text, 'ctr': ctr, 'spend': spend})
        if len(titles_with_metrics) >= 2:
            best_title = max(titles_with_metrics, key=lambda x: x['ctr'])
            worst_title = min(titles_with_metrics, key=lambda x: x['ctr'])
            insights.append(
                f'<b>Best headline by CTR:</b> "{best_title["text"]}" at '
                f'{fmt_pct(best_title["ctr"])} CTR ({fmt_money(best_title["spend"])} spend).'
            )
            insights.append(
                f'<b>Weakest headline by CTR:</b> "{worst_title["text"]}" at '
                f'{fmt_pct(worst_title["ctr"])} CTR.'
            )
            if worst_title['ctr'] > 0:
                ctr_advantage = (best_title['ctr'] - worst_title['ctr']) / worst_title['ctr']
                if ctr_advantage > 0.30:
                    insights.append(
                        f'<b>Headline recommendation:</b> Top headline has '
                        f'{ctr_advantage:.0%} higher CTR. Focus ad spend on '
                        f'"{best_title["text"]}" and consider pausing the weaker variant.'
                    )

    # --- Primary text insights ---
    if body_data:
        bodies_with_metrics = []
        for row in body_data:
            text = truncate_text(row.get('body_asset', {}).get('text', row.get('ad_name', 'Unknown')), 60)
            full_text = row.get('body_asset', {}).get('text', '')
            spend = float(row.get('spend', 0))
            ctr = float(row.get('ctr', 0))
            if spend > 1.0:
                bodies_with_metrics.append({
                    'text': text, 'ctr': ctr, 'spend': spend,
                    'is_long': len(full_text) > 200
                })
        if len(bodies_with_metrics) >= 2:
            best_body = max(bodies_with_metrics, key=lambda x: x['ctr'])
            worst_body = min(bodies_with_metrics, key=lambda x: x['ctr'])
            insights.append(
                f'<b>Best primary text by CTR:</b> "{best_body["text"]}" at '
                f'{fmt_pct(best_body["ctr"])} CTR ({fmt_money(best_body["spend"])} spend).'
            )
            insights.append(
                f'<b>Weakest primary text by CTR:</b> "{worst_body["text"]}" at '
                f'{fmt_pct(worst_body["ctr"])} CTR.'
            )
            # Check if long-form outperforms short-form
            long_forms = [b for b in bodies_with_metrics if b['is_long']]
            short_forms = [b for b in bodies_with_metrics if not b['is_long']]
            if long_forms and short_forms:
                avg_long_ctr = sum(b['ctr'] for b in long_forms) / len(long_forms)
                avg_short_ctr = sum(b['ctr'] for b in short_forms) / len(short_forms)
                if avg_long_ctr > avg_short_ctr:
                    insights.append(
                        f'<b>Copy length insight:</b> Long-form primary text ({fmt_pct(avg_long_ctr)} avg CTR) '
                        f'outperforms short-form ({fmt_pct(avg_short_ctr)} avg CTR). '
                        f'Lean into detailed storytelling copy.'
                    )
                elif avg_short_ctr > avg_long_ctr:
                    insights.append(
                        f'<b>Copy length insight:</b> Short-form primary text ({fmt_pct(avg_short_ctr)} avg CTR) '
                        f'outperforms long-form ({fmt_pct(avg_long_ctr)} avg CTR). '
                        f'Keep copy concise and punchy.'
                    )

    # --- Description insights ---
    if desc_data:
        descs_with_metrics = []
        for row in desc_data:
            text = truncate_text(row.get('description_asset', {}).get('text', row.get('ad_name', 'Unknown')), 60)
            spend = float(row.get('spend', 0))
            ctr = float(row.get('ctr', 0))
            if spend > 1.0:
                descs_with_metrics.append({'text': text, 'ctr': ctr, 'spend': spend})
        if len(descs_with_metrics) >= 2:
            best_desc = max(descs_with_metrics, key=lambda x: x['ctr'])
            worst_desc = min(descs_with_metrics, key=lambda x: x['ctr'])
            insights.append(
                f'<b>Best description by CTR:</b> "{best_desc["text"]}" at '
                f'{fmt_pct(best_desc["ctr"])} CTR ({fmt_money(best_desc["spend"])} spend).'
            )
            insights.append(
                f'<b>Weakest description by CTR:</b> "{worst_desc["text"]}" at '
                f'{fmt_pct(worst_desc["ctr"])} CTR.'
            )

    # --- Campaign comparison ---
    if len(campaigns) >= 2:
        objectives = set(get_objective_label(c) for c in campaigns)
        if len(objectives) > 1:
            for c in campaigns:
                obj = get_objective_label(c)
                lc_cpc = calc_link_cpc(c)
                insights.append(
                    f'<b>{obj} campaign:</b> "{c.get("campaign_name", "N/A")}" — '
                    f'{fmt_money(c.get("spend", 0))} spend, {fmt_number(extract_link_clicks(c))} link clicks, '
                    f'{fmt_pct(c.get("ctr", 0))} CTR, {fmt_money(lc_cpc)} CPC (Link). '
                    f'<i>Note: {obj} campaigns optimize for different actions, so CPC comparisons across objectives are not apples-to-apples.</i>'
                )
        else:
            sorted_camps = sorted(campaigns, key=lambda c: calc_link_cpc(c) if calc_link_cpc(c) > 0 else 999)
            best_camp = sorted_camps[0]
            worst_camp = sorted_camps[-1]
            if best_camp.get('campaign_name') != worst_camp.get('campaign_name'):
                insights.append(
                    f'<b>Campaign comparison:</b> "{best_camp.get("campaign_name", "N/A")}" '
                    f'outperforms at {fmt_money(calc_link_cpc(best_camp))} CPC (Link) vs '
                    f'"{worst_camp.get("campaign_name", "N/A")}" at {fmt_money(calc_link_cpc(worst_camp))} CPC (Link). '
                    f'Both are {list(objectives)[0]} campaigns, so this is a direct comparison.'
                )

    # --- Per-objective benchmarks ---
    # Group campaigns by objective for fair benchmarking
    obj_groups = {}
    for c in campaigns:
        obj = get_objective_label(c)
        if obj not in obj_groups:
            obj_groups[obj] = {'spend': 0, 'link_clicks': 0, 'impressions': 0, 'clicks': 0}
        obj_groups[obj]['spend'] += float(c.get('spend', 0))
        obj_groups[obj]['link_clicks'] += extract_link_clicks(c)
        obj_groups[obj]['impressions'] += int(c.get('impressions', 0))
        obj_groups[obj]['clicks'] += int(c.get('clicks', 0))

    for obj, stats in obj_groups.items():
        obj_ctr = (stats['clicks'] / stats['impressions'] * 100) if stats['impressions'] else 0
        obj_link_cpc = (stats['spend'] / stats['link_clicks']) if stats['link_clicks'] else 0

        if obj in ('Traffic', 'Engagement'):
            cpc_good, cpc_mod = 0.50, 1.00
            cpc_context = 'traffic campaigns'
        elif obj in ('Leads',):
            cpc_good, cpc_mod = 5.00, 15.00
            cpc_context = 'lead generation campaigns (leads cost more than clicks — this is expected)'
        elif obj in ('Sales', 'Conversions'):
            cpc_good, cpc_mod = 2.00, 5.00
            cpc_context = 'conversion campaigns'
        else:
            cpc_good, cpc_mod = 1.00, 3.00
            cpc_context = 'campaigns'

        if obj_ctr >= 2.0:
            insights.append(
                f'<b>{obj} CTR:</b> {fmt_pct(obj_ctr)} — strong engagement for {cpc_context}.'
            )
        elif obj_ctr >= 1.0:
            insights.append(
                f'<b>{obj} CTR:</b> {fmt_pct(obj_ctr)} — moderate. Consider testing new creatives.'
            )
        elif stats['impressions'] > 100:
            insights.append(
                f'<b>{obj} CTR:</b> {fmt_pct(obj_ctr)} — below 1%. Refresh creatives or adjust targeting.'
            )

        if stats['link_clicks'] > 0:
            if obj_link_cpc <= cpc_good:
                insights.append(
                    f'<b>{obj} CPC (Link):</b> {fmt_money(obj_link_cpc)} — efficient for {cpc_context}.'
                )
            elif obj_link_cpc <= cpc_mod:
                insights.append(
                    f'<b>{obj} CPC (Link):</b> {fmt_money(obj_link_cpc)} — moderate for {cpc_context}. Watch for rising costs.'
                )
            else:
                insights.append(
                    f'<b>{obj} CPC (Link):</b> {fmt_money(obj_link_cpc)} — high for {cpc_context}. Consider testing new creatives or audiences.'
                )

    # --- Generate Top 3 Actions (prioritized) ---
    actions = []

    # Priority 1: Creative image CTR gap > 30%
    if image_data:
        imgs = []
        for row in image_data:
            img_name = clean_image_name(row.get('image_asset', {}).get('name', row.get('ad_name', 'Unknown')))
            ctr = float(row.get('ctr', 0))
            spend = float(row.get('spend', 0))
            if spend > 0:
                imgs.append({'name': img_name, 'ctr': ctr, 'spend': spend})
        if len(imgs) >= 2:
            best_img = max(imgs, key=lambda x: x['ctr'])
            worst_img = min(imgs, key=lambda x: x['ctr'])
            if worst_img['ctr'] > 0 and (best_img['ctr'] - worst_img['ctr']) / worst_img['ctr'] > 0.30:
                gap = (best_img['ctr'] - worst_img['ctr']) / worst_img['ctr']
                actions.append(
                    f'<b>Scale spend toward "{best_img["name"]}" and pause "{worst_img["name"]}"</b> '
                    f'— {gap:.0%} CTR gap ({fmt_pct(best_img["ctr"])} vs {fmt_pct(worst_img["ctr"])})'
                )

    # Priority 2: Headline CTR gap > 30%
    if title_data:
        titles = []
        for row in title_data:
            text = truncate_text(row.get('title_asset', {}).get('text', row.get('ad_name', 'Unknown')), 50)
            ctr = float(row.get('ctr', 0))
            spend = float(row.get('spend', 0))
            if spend > 1.0:
                titles.append({'text': text, 'ctr': ctr})
        if len(titles) >= 2:
            best_t = max(titles, key=lambda x: x['ctr'])
            worst_t = min(titles, key=lambda x: x['ctr'])
            if worst_t['ctr'] > 0 and (best_t['ctr'] - worst_t['ctr']) / worst_t['ctr'] > 0.30:
                gap = (best_t['ctr'] - worst_t['ctr']) / worst_t['ctr']
                actions.append(
                    f'<b>Pin "{best_t["text"]}" as the primary headline</b> '
                    f'— {gap:.0%} higher CTR than the weakest headline ({fmt_pct(best_t["ctr"])} vs {fmt_pct(worst_t["ctr"])})'
                )

    # Priority 3: Age/gender segment CPC (Link) gap > 30%
    if age_gender_data:
        segments = {}
        for row in age_gender_data:
            if row.get('gender', 'unknown').lower() == 'unknown':
                continue
            seg_key = f'{row.get("gender", "unknown").title()} {row.get("age", "Unknown")}'
            spend = float(row.get('spend', 0))
            lc = extract_link_clicks(row)
            if seg_key not in segments:
                segments[seg_key] = {'spend': 0, 'link_clicks': 0}
            segments[seg_key]['spend'] += spend
            segments[seg_key]['link_clicks'] += lc
        segs_with_lc = {k: v for k, v in segments.items() if v['link_clicks'] > 0}
        if len(segs_with_lc) >= 2:
            cpcs = {k: v['spend'] / v['link_clicks'] for k, v in segs_with_lc.items()}
            best_seg = min(cpcs, key=cpcs.get)
            worst_seg = max(cpcs, key=cpcs.get)
            if cpcs[best_seg] > 0 and (cpcs[worst_seg] - cpcs[best_seg]) / cpcs[best_seg] > 0.30:
                actions.append(
                    f'<b>Create a dedicated ad set targeting {best_seg}</b> '
                    f'— best CPC (Link) at {fmt_money(cpcs[best_seg])} vs {fmt_money(cpcs[worst_seg])} for {worst_seg}'
                )

    # Priority 4: Placement burning budget with no/few clicks
    if platform_data:
        zero_lc_placements = []
        for row in platform_data:
            spend = float(row.get('spend', 0))
            lc = extract_link_clicks(row)
            if spend > 1.00 and lc == 0:
                name = clean_placement_name(row.get('publisher_platform', ''), row.get('platform_position', ''))
                zero_lc_placements.append({'name': name, 'spend': spend})
        if zero_lc_placements:
            names = ', '.join(p['name'] for p in zero_lc_placements[:3])
            wasted = sum(p['spend'] for p in zero_lc_placements)
            actions.append(
                f'<b>Exclude {names} from ad delivery</b> '
                f'— {fmt_money(wasted)} spent with zero link clicks'
            )

    # Priority 5: Primary text variant outperforming
    if body_data:
        bodies = []
        for row in body_data:
            full_text = row.get('body_asset', {}).get('text', '')
            ctr = float(row.get('ctr', 0))
            spend = float(row.get('spend', 0))
            if spend > 1.0:
                bodies.append({'ctr': ctr, 'is_long': len(full_text) > 200})
        long_forms = [b for b in bodies if b['is_long']]
        short_forms = [b for b in bodies if not b['is_long']]
        if long_forms and short_forms:
            avg_long = sum(b['ctr'] for b in long_forms) / len(long_forms)
            avg_short = sum(b['ctr'] for b in short_forms) / len(short_forms)
            if avg_long > avg_short:
                actions.append(
                    f'<b>Focus on long-form primary text</b> '
                    f'— averaging {fmt_pct(avg_long)} CTR vs {fmt_pct(avg_short)} for short-form'
                )
            elif avg_short > avg_long:
                actions.append(
                    f'<b>Focus on short-form primary text</b> '
                    f'— averaging {fmt_pct(avg_short)} CTR vs {fmt_pct(avg_long)} for long-form'
                )

    # Priority 6 & 7: Per-objective scaling/efficiency recommendations
    obj_groups = {}
    for c in campaigns:
        obj = get_objective_label(c)
        if obj not in obj_groups:
            obj_groups[obj] = {'spend': 0, 'link_clicks': 0, 'impressions': 0, 'clicks': 0}
        obj_groups[obj]['spend'] += float(c.get('spend', 0))
        obj_groups[obj]['link_clicks'] += extract_link_clicks(c)
        obj_groups[obj]['impressions'] += int(c.get('impressions', 0))
        obj_groups[obj]['clicks'] += int(c.get('clicks', 0))

    for obj, stats in obj_groups.items():
        obj_ctr = (stats['clicks'] / stats['impressions'] * 100) if stats['impressions'] else 0
        obj_link_cpc = (stats['spend'] / stats['link_clicks']) if stats['link_clicks'] else 0

        if obj in ('Traffic', 'Engagement'):
            cpc_threshold = 0.50
        elif obj in ('Leads',):
            cpc_threshold = 10.00
        elif obj in ('Sales', 'Conversions'):
            cpc_threshold = 3.00
        else:
            cpc_threshold = 2.00

        if obj_ctr > 2.0 and len(actions) < 5:
            actions.append(
                f'<b>Consider increasing {obj} campaign budget</b> '
                f'— strong {fmt_pct(obj_ctr)} CTR suggests room to scale'
            )

        if obj_link_cpc > cpc_threshold and stats['link_clicks'] > 0 and len(actions) < 5:
            actions.append(
                f'<b>Test new creatives in {obj} campaigns</b> '
                f'— CPC (Link) of {fmt_money(obj_link_cpc)} is above the {fmt_money(cpc_threshold)} target for {obj.lower()} campaigns'
            )

    top_3_actions = actions[:3]

    return insights, top_3_actions


# ---------------------------------------------------------------------------
# Standard table style builder
# ---------------------------------------------------------------------------

def make_table_style():
    """Return a consistent TableStyle matching the TKBS brand."""
    return TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND_CHARCOAL),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, BRAND_LIGHT]),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#dddddd')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ])


def color_code_table(style, data_rows, metric_col_index, mode='ctr'):
    """
    Apply green background to the best row and red to the worst row
    based on a metric column. mode='ctr' means higher is better,
    mode='cpc' means lower is better.

    data_rows: list of dicts with the raw data (same order as table rows)
    metric_col_index: which column has the metric to compare (unused, metric
                      is read from the dict key based on mode)
    style: the TableStyle object to modify in-place

    Only applies if there are 3+ data rows (with only 2 rows, the contrast
    is obvious enough).
    """
    if len(data_rows) < 3:
        return

    if mode == 'ctr':
        values = [float(row.get('ctr', 0)) for row in data_rows]
        best_idx = max(range(len(values)), key=lambda i: values[i])
        worst_idx = min(range(len(values)), key=lambda i: values[i])
    elif mode == 'cpc':
        values = [calc_link_cpc(row) if calc_link_cpc(row) > 0 else 999 for row in data_rows]
        best_idx = min(range(len(values)), key=lambda i: values[i])
        worst_idx = max(range(len(values)), key=lambda i: values[i])
    else:
        return

    # +1 offset accounts for the header row at index 0
    style.add('BACKGROUND', (0, best_idx + 1), (-1, best_idx + 1), BEST_ROW)
    style.add('BACKGROUND', (0, worst_idx + 1), (-1, worst_idx + 1), WORST_ROW)


# ---------------------------------------------------------------------------
# PDF builder
# ---------------------------------------------------------------------------

def build_pdf(output_path, days, account_info, campaigns, adsets, ads, daily,
              image_data, age_gender_data, platform_data,
              body_data=None, title_data=None, desc_data=None):
    doc = SimpleDocTemplate(
        output_path, pagesize=letter,
        topMargin=0.5*inch, bottomMargin=0.5*inch,
        leftMargin=0.6*inch, rightMargin=0.6*inch
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('ReportTitle', fontSize=22, fontName='Helvetica-Bold',
                               textColor=BRAND_CHARCOAL, spaceAfter=10))
    styles.add(ParagraphStyle('ReportSubtitle', fontSize=11, fontName='Helvetica',
                               textColor=BRAND_GRAY, spaceBefore=14, spaceAfter=16))
    styles.add(ParagraphStyle('SectionHead', fontSize=14, fontName='Helvetica-Bold',
                               textColor=BRAND_CHARCOAL, spaceBefore=16, spaceAfter=8))
    styles.add(ParagraphStyle('MetricLabel', fontSize=9, fontName='Helvetica',
                               textColor=BRAND_GRAY))
    styles.add(ParagraphStyle('MetricValue', fontSize=16, fontName='Helvetica-Bold',
                               textColor=BRAND_DARK, wordWrap='CJK'))
    styles['BodyText'].fontSize = 10
    styles['BodyText'].fontName = 'Helvetica'
    styles['BodyText'].textColor = BRAND_DARK
    styles['BodyText'].leading = 14
    styles.add(ParagraphStyle('InsightBullet', fontSize=10, fontName='Helvetica',
                               textColor=BRAND_DARK, leading=14,
                               spaceBefore=2, spaceAfter=4,
                               leftIndent=12, bulletIndent=0))
    styles.add(ParagraphStyle('TableHeader', fontSize=9, fontName='Helvetica-Bold',
                               textColor=WHITE))
    styles.add(ParagraphStyle('TableCell', fontSize=9, fontName='Helvetica',
                               textColor=BRAND_DARK))
    styles.add(ParagraphStyle('Footer', fontSize=8, fontName='Helvetica',
                               textColor=BRAND_GRAY, alignment=TA_CENTER))

    story = []
    today_str = datetime.now().strftime('%B %d, %Y')

    # -----------------------------------------------------------------------
    # 1. Header
    # -----------------------------------------------------------------------
    story.append(Paragraph(CLIENT_NAME, styles['ReportTitle']))
    story.append(Paragraph(
        f'Ad Performance Report  |  Last {days} Days  |  {today_str}',
        styles['ReportSubtitle']
    ))
    story.append(HRFlowable(width='100%', thickness=2, color=BRAND_MINT, spaceAfter=16))

    # -----------------------------------------------------------------------
    # Compute summary metrics (needed by executive summary and metrics grid)
    # -----------------------------------------------------------------------
    total_spend = sum(float(c.get('spend', 0)) for c in campaigns)
    total_impressions = sum(int(c.get('impressions', 0)) for c in campaigns)
    total_reach = sum(int(c.get('reach', 0)) for c in campaigns)
    total_clicks = sum(int(c.get('clicks', 0)) for c in campaigns)
    total_link_clicks = sum(extract_link_clicks(c) for c in campaigns)
    # Link CTR (link clicks / impressions) so the headline metrics reconcile with each other
    avg_ctr = (total_link_clicks / total_impressions * 100) if total_impressions else 0
    avg_cpc = (total_spend / total_link_clicks) if total_link_clicks else 0
    cost_per_link = (total_spend / total_link_clicks) if total_link_clicks else 0

    # Sales / conversion totals
    total_purchases = sum(extract_purchases(c) for c in campaigns)
    total_add_to_cart = sum(extract_add_to_cart(c) for c in campaigns)
    total_checkouts = sum(extract_initiate_checkout(c) for c in campaigns)
    total_revenue = sum(extract_purchase_value(c) for c in campaigns)
    total_roas = (total_revenue / total_spend) if total_spend else 0
    cost_per_purchase = (total_spend / total_purchases) if total_purchases else 0

    # The selected profile drives the report's headline layout (summary grid,
    # exec card, campaign table, daily trend). Everything else is shared.
    profile = select_profile(campaigns)
    totals = {
        'spend': total_spend,
        'purchases': total_purchases,
        'add_to_cart': total_add_to_cart,
        'checkouts': total_checkouts,
        'revenue': total_revenue,
        'roas': total_roas,
        'cost_per_purchase': cost_per_purchase,
    }

    # -----------------------------------------------------------------------
    # Generate insights EARLY so top_3_actions are available for exec summary
    # -----------------------------------------------------------------------
    insights, top_3_actions = generate_insights(
        campaigns, image_data, age_gender_data, platform_data,
        total_spend, total_link_clicks, avg_ctr, avg_cpc,
        body_data=body_data, title_data=title_data, desc_data=desc_data
    )

    # -----------------------------------------------------------------------
    # 2a. Executive Summary (page 1 — scannable overview)
    # -----------------------------------------------------------------------

    # -- Prepare daily sparkline data --
    sorted_daily = sorted(daily, key=lambda x: x.get('date_start', '')) if daily else []
    daily_spends = [float(d.get('spend', 0)) for d in sorted_daily]
    daily_ctrs = [float(d.get('ctr', 0)) for d in sorted_daily]

    # -- Add ExecSummary-specific styles --
    styles.add(ParagraphStyle('ExecMetric', fontSize=10, fontName='Helvetica',
                               textColor=BRAND_DARK, leading=14))
    styles.add(ParagraphStyle('ExecObjTitle', fontSize=12, fontName='Helvetica-Bold',
                               textColor=BRAND_CHARCOAL, spaceBefore=6, spaceAfter=2))
    styles.add(ParagraphStyle('ExecCampaignList', fontSize=8, fontName='Helvetica',
                               textColor=BRAND_GRAY, leading=11))
    styles.add(ParagraphStyle('ExecActionTitle', fontSize=11, fontName='Helvetica-Bold',
                               textColor=BRAND_CHARCOAL, spaceBefore=4, spaceAfter=4))
    styles.add(ParagraphStyle('ExecAction', fontSize=10, fontName='Helvetica',
                               textColor=BRAND_DARK, leading=14,
                               spaceBefore=2, spaceAfter=3))
    styles.add(ParagraphStyle('ExecAlertTitle', fontSize=11, fontName='Helvetica-Bold',
                               textColor=BRAND_CHARCOAL, spaceBefore=4, spaceAfter=4))
    styles.add(ParagraphStyle('ExecAlert', fontSize=9, fontName='Helvetica',
                               textColor=BRAND_DARK, leading=13,
                               spaceBefore=1, spaceAfter=2))

    exec_elements = []
    exec_elements.append(Paragraph('Executive Summary', styles['SectionHead']))

    # -- Group campaigns by objective --
    obj_groups_exec = {}
    for c in campaigns:
        obj = get_objective_label(c)
        if obj not in obj_groups_exec:
            obj_groups_exec[obj] = {
                'spend': 0, 'impressions': 0, 'reach': 0,
                'link_clicks': 0, 'clicks': 0, 'campaigns': []
            }
        obj_groups_exec[obj]['spend'] += float(c.get('spend', 0))
        obj_groups_exec[obj]['impressions'] += int(c.get('impressions', 0))
        obj_groups_exec[obj]['reach'] += int(c.get('reach', 0))
        obj_groups_exec[obj]['link_clicks'] += extract_link_clicks(c)
        obj_groups_exec[obj]['clicks'] += int(c.get('clicks', 0))
        obj_groups_exec[obj]['campaigns'].append(c.get('campaign_name', 'Unknown'))

    # -- Per-objective summary cards --
    primary_data = get_primary_metrics(campaigns)
    for obj, stats in primary_data.items():
        config = stats['config']
        thresholds = config['thresholds']

        # PRIMARY metric — the one that defines success for this objective
        primary_label = config['primary_label']
        primary_cost_label = config['primary_cost_label']
        primary_count = stats['primary_count']
        primary_cost = stats['primary_cost']

        # Traffic light on the PRIMARY cost metric
        cost_key = config['primary_cost']  # e.g., 'cpc_link' or 'cost_per_lpv'
        cost_thresholds = thresholds.get(cost_key, thresholds.get('cpc_link', (1.00, 3.00)))
        cost_color = traffic_light(primary_cost, cost_thresholds, mode='lower_is_better')

        # CTR traffic light (secondary)
        ctr_thresholds = thresholds.get('ctr', (2.0, 1.0))
        ctr_color = traffic_light(stats['ctr'], ctr_thresholds, mode='higher_is_better')

        # Build metric lines — PRIMARY metric first and largest
        primary_text = (
            f'<font color="{cost_color}" size="14">&#9679;</font> '
            f'<b>{primary_cost_label}: {fmt_money(primary_cost)}</b> '
            f'({fmt_number(primary_count)} {primary_label})'
        )
        secondary_text = (
            f'<font color="{ctr_color}">&#9679;</font> CTR: {fmt_pct(stats["ctr"])} '
            f'&nbsp;&nbsp; Spend: {fmt_money(stats["spend"])}'
        )

        metrics_line = Paragraph(primary_text, styles['ExecMetric'])
        secondary_line = Paragraph(secondary_text, styles['ExecMetric'])

        # Objective-specific highlight line (e.g. ROAS for Sales campaigns)
        extra_line = profile_for_objective(obj).exec_line(stats, styles)

        # Sparklines for right column
        sparkline_ctr = make_sparkline(daily_ctrs, width=120, height=25, color=BRAND_MINT)
        sparkline_spend = make_sparkline(daily_spends, width=120, height=25, color=BRAND_CHARCOAL)

        # Build the sparkline column content
        sparkline_elements = []
        if sparkline_ctr:
            sparkline_elements.append(Paragraph('<font size="7" color="#666666">Daily CTR trend</font>', styles['ExecCampaignList']))
            sparkline_elements.append(sparkline_ctr)
        if sparkline_spend:
            sparkline_elements.append(Paragraph('<font size="7" color="#666666">Daily spend trend</font>', styles['ExecCampaignList']))
            sparkline_elements.append(sparkline_spend)

        # Campaign list
        camp_names = ', '.join(stats['campaigns'])
        camp_list = Paragraph(f'Campaigns: {camp_names}', styles['ExecCampaignList'])

        # Build a 2-column layout: left = metrics, right = sparklines
        left_content = [metrics_line, Spacer(1, 2), secondary_line]
        if extra_line is not None:
            left_content += [Spacer(1, 2), extra_line]
        left_content += [Spacer(1, 4), camp_list]
        right_content = sparkline_elements if sparkline_elements else [Spacer(1, 1)]

        # Use a nested table for left content
        left_table = Table([[item] for item in left_content], colWidths=[USABLE_WIDTH * 0.62])
        left_table.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))

        right_table = Table([[item] for item in right_content], colWidths=[USABLE_WIDTH * 0.35])
        right_table.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))

        # Objective title
        exec_elements.append(Paragraph(f'{obj} Campaigns', styles['ExecObjTitle']))
        exec_elements.append(HRFlowable(width='100%', thickness=1.5, color=BRAND_CHARCOAL, spaceAfter=4))

        # 2-column card table
        card_table = Table(
            [[left_table, right_table]],
            colWidths=[USABLE_WIDTH * 0.63, USABLE_WIDTH * 0.37]
        )
        card_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), BRAND_LIGHT),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('ROUNDEDCORNERS', [4, 4, 4, 4]),
        ]))
        exec_elements.append(card_table)
        exec_elements.append(Spacer(1, 8))

    # -- Top 3 Actions box (mint left border, light mint background) --
    if top_3_actions:
        action_items = []
        action_items.append(Paragraph('Recommended Actions', styles['ExecActionTitle']))
        for i, action in enumerate(top_3_actions, 1):
            action_items.append(Paragraph(f'{i}. {action}', styles['ExecAction']))

        action_inner_table = Table([[item] for item in action_items],
                                    colWidths=[USABLE_WIDTH - 18])
        action_inner_table.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))

        action_box = Table([[action_inner_table]], colWidths=[USABLE_WIDTH - 8])
        action_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f0fdf9')),
            ('LEFTPADDING', (0, 0), (-1, -1), 14),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LINEBEFORESTARTOFFSET', (0, 0), (0, -1), 0),
            ('LINEBEFORE', (0, 0), (0, -1), 4, BRAND_MINT),
            ('ROUNDEDCORNERS', [0, 4, 4, 0]),
        ]))
        exec_elements.append(action_box)
        exec_elements.append(Spacer(1, 8))

    # -- Quick Wins / Alerts box --
    alert_items = []

    # Best performing creative (by CTR)
    if image_data:
        imgs_with_ctr = []
        for row in image_data:
            img_name = clean_image_name(row.get('image_asset', {}).get('name', row.get('ad_name', 'Unknown')))
            ctr = float(row.get('ctr', 0))
            spend = float(row.get('spend', 0))
            if spend > 0:
                imgs_with_ctr.append({'name': img_name, 'ctr': ctr})
        if imgs_with_ctr:
            best_creative = max(imgs_with_ctr, key=lambda x: x['ctr'])
            # Use default thresholds for the creative alert
            ctr_thresh = METRIC_THRESHOLDS.get('default', {}).get('ctr', (2.0, 1.0))
            creative_color = traffic_light(best_creative['ctr'], ctr_thresh, mode='higher_is_better')
            alert_items.append(Paragraph(
                f'<font color="{creative_color}">&#9679;</font> '
                f'<b>Best creative:</b> "{best_creative["name"]}" at {fmt_pct(best_creative["ctr"])} CTR',
                styles['ExecAlert']
            ))

    # Best performing audience segment
    if age_gender_data:
        segments = {}
        for row in age_gender_data:
            if row.get('gender', 'unknown').lower() == 'unknown':
                continue
            seg_key = f'{row.get("gender", "unknown").title()} {row.get("age", "Unknown")}'
            spend = float(row.get('spend', 0))
            lc = extract_link_clicks(row)
            if seg_key not in segments:
                segments[seg_key] = {'spend': 0, 'link_clicks': 0}
            segments[seg_key]['spend'] += spend
            segments[seg_key]['link_clicks'] += lc
        segs_with_lc = {k: v for k, v in segments.items() if v['link_clicks'] > 0}
        if segs_with_lc:
            best_seg_key = min(segs_with_lc, key=lambda k: segs_with_lc[k]['spend'] / segs_with_lc[k]['link_clicks'])
            best_seg_cpc = segs_with_lc[best_seg_key]['spend'] / segs_with_lc[best_seg_key]['link_clicks']
            alert_items.append(Paragraph(
                f'<font color="{COLOR_GREEN}">&#9679;</font> '
                f'<b>Best audience:</b> {best_seg_key} at {fmt_money(best_seg_cpc)} CPC (Link)',
                styles['ExecAlert']
            ))

    # Placements wasting budget (red alert)
    if platform_data:
        wasting_placements = []
        for row in platform_data:
            spend = float(row.get('spend', 0))
            lc = extract_link_clicks(row)
            if spend > 1.00 and lc == 0:
                name = clean_placement_name(row.get('publisher_platform', ''), row.get('platform_position', ''))
                wasting_placements.append({'name': name, 'spend': spend})
        if wasting_placements:
            wasted_total = sum(p['spend'] for p in wasting_placements)
            names = ', '.join(p['name'] for p in wasting_placements[:3])
            alert_items.append(Paragraph(
                f'<font color="{COLOR_RED}">&#9679;</font> '
                f'<b>Budget waste:</b> {names} spent {fmt_money(wasted_total)} with zero link clicks',
                styles['ExecAlert']
            ))

    if alert_items:
        alert_items.insert(0, Paragraph('Quick Wins &amp; Alerts', styles['ExecAlertTitle']))
        alert_inner_table = Table([[item] for item in alert_items],
                                   colWidths=[USABLE_WIDTH - 18])
        alert_inner_table.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))
        alert_box = Table([[alert_inner_table]], colWidths=[USABLE_WIDTH - 8])
        alert_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), BRAND_LIGHT),
            ('LEFTPADDING', (0, 0), (-1, -1), 14),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('ROUNDEDCORNERS', [4, 4, 4, 4]),
        ]))
        exec_elements.append(alert_box)
        exec_elements.append(Spacer(1, 12))

    story.append(KeepTogether(exec_elements))

    # -----------------------------------------------------------------------
    # 2b. Summary Metrics Grid
    # -----------------------------------------------------------------------

    def metric_cell(label, value):
        return [
            Paragraph(label, styles['MetricLabel']),
            Paragraph(str(value), styles['MetricValue'])
        ]

    metrics_data = [
        metric_cell('Total Spend', fmt_money(total_spend)),
        metric_cell('Impressions', fmt_number(total_impressions)),
        metric_cell('Reach', fmt_number(total_reach)),
        metric_cell('Link Clicks', fmt_number(total_link_clicks)),
        metric_cell('Link CTR', fmt_pct(avg_ctr)),
        metric_cell('CPC (Link)', fmt_money(avg_cpc)),
    ]
    metrics_data += profile.summary_cells(totals, metric_cell)

    metric_table_data = [
        [m[0] for m in metrics_data],
        [m[1] for m in metrics_data],
    ]

    metric_col_widths = [USABLE_WIDTH / len(metrics_data)] * len(metrics_data)
    metric_table = Table(metric_table_data, colWidths=metric_col_widths)
    metric_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BRAND_LIGHT),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 10),
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
    ]))
    story.append(metric_table)
    story.append(Spacer(1, 12))

    # -----------------------------------------------------------------------
    # 3. Campaign Performance
    # -----------------------------------------------------------------------
    section_elements = []
    section_elements.append(Paragraph('Campaign Performance', styles['SectionHead']))

    camp_rows, camp_col_widths = profile.campaign_table(campaigns, styles, USABLE_WIDTH)
    camp_table = Table(camp_rows, colWidths=camp_col_widths, repeatRows=1)
    camp_style = make_table_style()
    color_code_table(camp_style, campaigns, metric_col_index=0, mode='cpc')
    camp_table.setStyle(camp_style)
    section_elements.append(camp_table)
    section_elements.append(Spacer(1, 12))
    story.append(KeepTogether(section_elements))

    # -----------------------------------------------------------------------
    # 4. Creative Element Performance
    # -----------------------------------------------------------------------
    if image_data:
        # Dynamic creative — use image_asset breakdown
        section_elements = []
        section_elements.append(Paragraph('Creative Element Performance', styles['SectionHead']))

        img_header = ['', 'Image Name', 'Spend', 'Link Clicks', 'CTR', 'CPC (Link)']
        img_rows = [img_header]
        for row in image_data:
            asset = row.get('image_asset', {})
            img_name = clean_image_name(asset.get('name', row.get('ad_name', 'Unknown')))
            img_url = asset.get('url', '')
            lc = extract_link_clicks(row)
            thumb = download_thumbnail(img_url) if img_url else ''
            img_rows.append([
                thumb or '',
                Paragraph(img_name, styles['TableCell']),
                fmt_money(row.get('spend', 0)),
                fmt_number(lc),
                fmt_pct(calc_link_ctr(row)),
                fmt_money(calc_link_cpc(row)),
            ])

        img_col_widths = [1.2*inch, (USABLE_WIDTH - 1.2*inch - 3.15*inch), 0.75*inch, 0.9*inch, 0.75*inch, 0.75*inch]
        img_table = Table(img_rows, colWidths=img_col_widths, repeatRows=1,
                          rowHeights=[None] + [100] * (len(img_rows) - 1))
        img_style = make_table_style()
        img_style.add('VALIGN', (0, 1), (0, -1), 'MIDDLE')
        color_code_table(img_style, image_data, metric_col_index=4, mode='ctr')
        img_table.setStyle(img_style)
        section_elements.append(img_table)
        section_elements.append(Spacer(1, 12))
        story.append(KeepTogether(section_elements))

    if ads:
        # Ad-level creative breakdown with thumbnails (always show this)
        section_elements = []
        section_elements.append(Paragraph('Ad Creative Performance', styles['SectionHead']))

        ad_ids = [a.get('ad_id', '') for a in ads if a.get('ad_id')]
        thumbnails = fetch_ad_thumbnails(ad_ids) if ad_ids else {}

        cr_header = ['', 'Ad Creative', 'Campaign', 'Spend', 'Link Clicks', 'CTR', 'CPC (Link)']
        cr_rows = [cr_header]
        for a in ads:
            lc = extract_link_clicks(a)
            ad_id = a.get('ad_id', '')
            thumb_url = thumbnails.get(ad_id, '')
            thumb = download_thumbnail(thumb_url) if thumb_url else ''
            cr_rows.append([
                thumb or '',
                Paragraph(a.get('ad_name', 'Unknown'), styles['TableCell']),
                Paragraph(truncate_text(a.get('campaign_name', ''), 30), styles['TableCell']),
                fmt_money(a.get('spend', 0)),
                fmt_number(lc),
                fmt_pct(calc_link_ctr(a)),
                fmt_money(calc_link_cpc(a)),
            ])

        cr_col_widths = [1.2*inch, (USABLE_WIDTH - 1.2*inch - 4.1*inch), 1.2*inch, 0.7*inch, 0.8*inch, 0.65*inch, 0.75*inch]
        cr_table = Table(cr_rows, colWidths=cr_col_widths, repeatRows=1,
                         rowHeights=[None] + [100] * (len(cr_rows) - 1))
        cr_style = make_table_style()
        cr_style.add('VALIGN', (0, 1), (0, -1), 'MIDDLE')
        color_code_table(cr_style, ads, metric_col_index=5, mode='ctr')
        cr_table.setStyle(cr_style)
        section_elements.append(cr_table)
        section_elements.append(Spacer(1, 12))
        story.append(KeepTogether(section_elements))

    # -----------------------------------------------------------------------
    # 5a. Headline Performance
    # -----------------------------------------------------------------------
    if title_data:
        filtered_titles = [row for row in title_data if float(row.get('spend', 0)) > 0.50]
        if filtered_titles:
            section_elements = []
            section_elements.append(Paragraph('Headline Performance', styles['SectionHead']))

            title_header = ['Headline', 'Spend', 'Link Clicks', 'CTR', 'CPC (Link)']
            title_rows = [title_header]
            for row in filtered_titles:
                text = truncate_text(row.get('title_asset', {}).get('text', row.get('ad_name', 'Unknown')), 50)
                lc = extract_link_clicks(row)
                title_rows.append([
                    Paragraph(text, styles['TableCell']),
                    fmt_money(row.get('spend', 0)),
                    fmt_number(lc),
                    fmt_pct(calc_link_ctr(row)),
                    fmt_money(calc_link_cpc(row)),
                ])

            # 5 cols: others = 0.8+0.9+0.7+0.7 = 3.1; first absorbs rest
            title_col_widths = [(USABLE_WIDTH - 3.1*inch), 0.8*inch, 0.9*inch, 0.7*inch, 0.7*inch]
            title_table = Table(title_rows, colWidths=title_col_widths, repeatRows=1)
            title_style = make_table_style()
            color_code_table(title_style, filtered_titles, metric_col_index=3, mode='ctr')
            title_table.setStyle(title_style)
            section_elements.append(title_table)
            section_elements.append(Spacer(1, 12))
            story.append(KeepTogether(section_elements))

    # -----------------------------------------------------------------------
    # 5b. Primary Text Performance
    # -----------------------------------------------------------------------
    if body_data:
        filtered_bodies = [row for row in body_data if float(row.get('spend', 0)) > 0.50]
        if filtered_bodies:
            section_elements = []
            section_elements.append(Paragraph('Primary Text Performance', styles['SectionHead']))

            body_header = ['Primary Text', 'Spend', 'Link Clicks', 'CTR', 'CPC (Link)']
            body_rows = [body_header]
            for row in filtered_bodies:
                text = truncate_text(row.get('body_asset', {}).get('text', row.get('ad_name', 'Unknown')), 60)
                lc = extract_link_clicks(row)
                body_rows.append([
                    Paragraph(text, styles['TableCell']),
                    fmt_money(row.get('spend', 0)),
                    fmt_number(lc),
                    fmt_pct(calc_link_ctr(row)),
                    fmt_money(calc_link_cpc(row)),
                ])

            # 5 cols: others = 0.8+0.9+0.7+0.7 = 3.1; first absorbs rest
            body_col_widths = [(USABLE_WIDTH - 3.1*inch), 0.8*inch, 0.9*inch, 0.7*inch, 0.7*inch]
            body_table = Table(body_rows, colWidths=body_col_widths, repeatRows=1)
            body_style = make_table_style()
            color_code_table(body_style, filtered_bodies, metric_col_index=3, mode='ctr')
            body_table.setStyle(body_style)
            section_elements.append(body_table)
            section_elements.append(Spacer(1, 12))
            story.append(KeepTogether(section_elements))

    # -----------------------------------------------------------------------
    # 5c. Description Performance
    # -----------------------------------------------------------------------
    if desc_data:
        filtered_descs = [row for row in desc_data if float(row.get('spend', 0)) > 0.50]
        if filtered_descs:
            section_elements = []
            section_elements.append(Paragraph('Description Performance', styles['SectionHead']))

            desc_header = ['Description', 'Spend', 'Link Clicks', 'CTR', 'CPC (Link)']
            desc_rows = [desc_header]
            for row in filtered_descs:
                text = truncate_text(row.get('description_asset', {}).get('text', row.get('ad_name', 'Unknown')), 60)
                lc = extract_link_clicks(row)
                desc_rows.append([
                    Paragraph(text, styles['TableCell']),
                    fmt_money(row.get('spend', 0)),
                    fmt_number(lc),
                    fmt_pct(calc_link_ctr(row)),
                    fmt_money(calc_link_cpc(row)),
                ])

            # 5 cols: others = 0.8+0.9+0.7+0.7 = 3.1; first absorbs rest
            desc_col_widths = [(USABLE_WIDTH - 3.1*inch), 0.8*inch, 0.9*inch, 0.7*inch, 0.7*inch]
            desc_table = Table(desc_rows, colWidths=desc_col_widths, repeatRows=1)
            desc_style = make_table_style()
            color_code_table(desc_style, filtered_descs, metric_col_index=3, mode='ctr')
            desc_table.setStyle(desc_style)
            section_elements.append(desc_table)
            section_elements.append(Spacer(1, 12))
            story.append(KeepTogether(section_elements))

    # -----------------------------------------------------------------------
    # 5. Audience Demographics
    # -----------------------------------------------------------------------
    if age_gender_data:
        section_elements = []
        section_elements.append(Paragraph('Audience Demographics', styles['SectionHead']))

        # Aggregate by age group (exclude unknown gender)
        age_agg = {}
        gender_agg = {}
        for row in age_gender_data:
            age = row.get('age', 'Unknown')
            gender = row.get('gender', 'unknown')
            if gender.lower() == 'unknown':
                continue
            spend = float(row.get('spend', 0))
            impressions = int(row.get('impressions', 0))
            clicks = int(row.get('clicks', 0))
            lc = extract_link_clicks(row)

            if age not in age_agg:
                age_agg[age] = {'spend': 0, 'impressions': 0, 'clicks': 0, 'link_clicks': 0}
            age_agg[age]['spend'] += spend
            age_agg[age]['impressions'] += impressions
            age_agg[age]['clicks'] += clicks
            age_agg[age]['link_clicks'] += lc

            seg_key = f'{gender.title()} {age}'
            if seg_key not in gender_agg:
                gender_agg[seg_key] = {'spend': 0, 'impressions': 0, 'clicks': 0, 'link_clicks': 0}
            gender_agg[seg_key]['spend'] += spend
            gender_agg[seg_key]['impressions'] += impressions
            gender_agg[seg_key]['clicks'] += clicks
            gender_agg[seg_key]['link_clicks'] += lc

        age_header = ['Age Group', 'Spend', 'Impressions', 'Link Clicks', 'CTR', 'CPC (Link)']
        age_rows = [age_header]
        for age in sorted(age_agg.keys()):
            d = age_agg[age]
            ctr = (d['link_clicks'] / d['impressions'] * 100) if d['impressions'] else 0
            cpc = d['spend'] / d['link_clicks'] if d['link_clicks'] > 0 else 0
            age_rows.append([
                age,
                fmt_money(d['spend']),
                fmt_number(d['impressions']),
                fmt_number(d['link_clicks']),
                fmt_pct(ctr),
                fmt_money(cpc),
            ])

        # 6 cols: others = 0.9+1.1+0.9+0.8+0.8 = 4.5; first absorbs rest
        age_col_widths = [(USABLE_WIDTH - 4.5*inch), 0.9*inch, 1.1*inch, 0.9*inch, 0.8*inch, 0.8*inch]
        age_table = Table(age_rows, colWidths=age_col_widths, repeatRows=1)
        age_table.setStyle(make_table_style())
        section_elements.append(age_table)

        # Top gender segment note (exclude unknown, require min $2 spend)
        gender_with_lc = {
            k: v for k, v in gender_agg.items()
            if v['link_clicks'] > 0 and k.lower() != 'unknown' and v['spend'] >= 2.0
        }
        if gender_with_lc:
            best_seg = min(gender_with_lc.items(), key=lambda x: x[1]['spend'] / x[1]['link_clicks'])
            seg_cpc = best_seg[1]['spend'] / best_seg[1]['link_clicks']
            seg_ctr = best_seg[1]['link_clicks'] / best_seg[1]['impressions'] * 100 if best_seg[1]['impressions'] else 0
            section_elements.append(Spacer(1, 4))
            section_elements.append(Paragraph(
                f'<b>Top segment:</b> {best_seg[0]} -- {fmt_pct(seg_ctr)} CTR, '
                f'{fmt_money(seg_cpc)} CPC (Link), {fmt_number(best_seg[1]["link_clicks"])} link clicks.',
                styles['BodyText']
            ))
        section_elements.append(Spacer(1, 12))
        story.append(KeepTogether(section_elements))

    # -----------------------------------------------------------------------
    # 6. Platform & Placement Performance
    # -----------------------------------------------------------------------
    if platform_data:
        # Filter to rows with > $0.50 spend
        filtered_placements = [
            row for row in platform_data if float(row.get('spend', 0)) > 0.50
        ]
        if filtered_placements:
            section_elements = []
            section_elements.append(Paragraph('Platform &amp; Placement Performance', styles['SectionHead']))

            plat_header = ['Platform / Placement', 'Spend', 'Impressions', 'Link Clicks', 'CTR', 'CPC (Link)']
            plat_rows = [plat_header]
            for row in sorted(filtered_placements, key=lambda x: float(x.get('spend', 0)), reverse=True):
                lc = extract_link_clicks(row)
                name = clean_placement_name(
                    row.get('publisher_platform', ''),
                    row.get('platform_position', '')
                )
                plat_rows.append([
                    Paragraph(name, styles['TableCell']),
                    fmt_money(row.get('spend', 0)),
                    fmt_number(row.get('impressions', 0)),
                    fmt_number(lc),
                    fmt_pct(calc_link_ctr(row)),
                    fmt_money(calc_link_cpc(row)),
                ])

            # 6 cols: others = 0.8+1.0+0.9+0.8+0.8 = 4.3; first absorbs rest
            plat_col_widths = [(USABLE_WIDTH - 4.3*inch), 0.8*inch, 1.0*inch, 0.9*inch, 0.8*inch, 0.8*inch]
            plat_table = Table(plat_rows, colWidths=plat_col_widths, repeatRows=1)
            sorted_placements = sorted(filtered_placements, key=lambda x: float(x.get('spend', 0)), reverse=True)
            plat_style = make_table_style()
            color_code_table(plat_style, sorted_placements, metric_col_index=4, mode='ctr')
            plat_table.setStyle(plat_style)
            section_elements.append(plat_table)
            section_elements.append(Spacer(1, 12))
            story.append(KeepTogether(section_elements))

    # -----------------------------------------------------------------------
    # 7. Ad Set Performance
    # -----------------------------------------------------------------------
    if adsets:
        section_elements = []
        section_elements.append(Paragraph('Ad Set Performance', styles['SectionHead']))
        adset_header = ['Ad Set', 'Spend', 'Reach', 'Link Clicks', 'CTR', 'CPC (Link)']
        adset_rows = [adset_header]
        for a in adsets:
            lc = extract_link_clicks(a)
            adset_rows.append([
                Paragraph(a.get('adset_name', 'Unknown'), styles['TableCell']),
                fmt_money(a.get('spend', 0)),
                fmt_number(a.get('reach', 0)),
                fmt_number(lc),
                fmt_pct(calc_link_ctr(a)),
                fmt_money(calc_link_cpc(a)),
            ])

        # 6 cols: others = 0.8+0.8+0.9+0.7+0.7 = 3.9; first absorbs rest
        adset_col_widths = [(USABLE_WIDTH - 3.9*inch), 0.8*inch, 0.8*inch, 0.9*inch, 0.7*inch, 0.7*inch]
        adset_table = Table(adset_rows, colWidths=adset_col_widths, repeatRows=1)
        adset_table.setStyle(make_table_style())
        section_elements.append(adset_table)
        section_elements.append(Spacer(1, 12))
        story.append(KeepTogether(section_elements))

    # -----------------------------------------------------------------------
    # 7b. Top Performing Ads
    # -----------------------------------------------------------------------
    if ads:
        section_elements = []
        section_elements.append(Paragraph('Top Performing Ads', styles['SectionHead']))
        ad_header = ['Ad Name', 'Spend', 'Link Clicks', 'CTR', 'CPC (Link)']
        ad_rows = [ad_header]
        for a in ads:
            lc = extract_link_clicks(a)
            ad_rows.append([
                Paragraph(truncate_text(a.get('ad_name', 'Unknown'), 50), styles['TableCell']),
                fmt_money(a.get('spend', 0)),
                fmt_number(lc),
                fmt_pct(calc_link_ctr(a)),
                fmt_money(calc_link_cpc(a)),
            ])

        # 5 cols: others = 0.8+0.9+0.7+0.7 = 3.1; first absorbs rest
        ad_col_widths = [(USABLE_WIDTH - 3.1*inch), 0.8*inch, 0.9*inch, 0.7*inch, 0.7*inch]
        ad_table = Table(ad_rows, colWidths=ad_col_widths, repeatRows=1)
        ad_table.setStyle(make_table_style())
        section_elements.append(ad_table)
        section_elements.append(Spacer(1, 12))
        story.append(KeepTogether(section_elements))

    # -----------------------------------------------------------------------
    # 8. Daily Trend
    # -----------------------------------------------------------------------
    if daily:
        section_elements = []
        section_elements.append(Paragraph('Daily Spend &amp; Performance', styles['SectionHead']))

        daily_rows, daily_col_widths = profile.daily_table(daily, USABLE_WIDTH)
        daily_table = Table(daily_rows, colWidths=daily_col_widths, repeatRows=1)
        daily_table.setStyle(make_table_style())
        section_elements.append(daily_table)
        section_elements.append(Spacer(1, 12))
        story.append(KeepTogether(section_elements))

    # -----------------------------------------------------------------------
    # 9. Insights & Recommendations
    # -----------------------------------------------------------------------
    story.append(Paragraph('Insights &amp; Recommendations', styles['SectionHead']))
    story.append(HRFlowable(width='100%', thickness=1, color=BRAND_MINT, spaceAfter=8))

    # insights and top_3_actions were already computed before the executive summary

    for insight in insights:
        story.append(Paragraph(f'•  {insight}', styles['InsightBullet']))

    if not insights:
        story.append(Paragraph(
            'Not enough data to generate insights. Run campaigns for a few more days.',
            styles['BodyText']
        ))

    # --- Top 3 Recommended Actions ---
    if top_3_actions:
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width='100%', thickness=0.5, color=BRAND_GRAY, spaceAfter=8))
        story.append(Paragraph('Recommended Actions', styles['SectionHead']))
        for i, action in enumerate(top_3_actions, 1):
            story.append(Paragraph(
                f'{i}. {action}',
                styles['InsightBullet']
            ))

    # -----------------------------------------------------------------------
    # 10. Footer
    # -----------------------------------------------------------------------
    story.append(Spacer(1, 24))
    story.append(HRFlowable(width='100%', thickness=1, color=HexColor('#dddddd'), spaceAfter=8))
    story.append(Paragraph(
        f'Generated by TKBS Marketing  |  {today_str}  |  Data source: Meta Marketing API',
        styles['Footer']
    ))

    doc.build(story)
    return output_path


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Generate a Meta ad performance report for any client. '
                    'One shared script — each client supplies a .env in its project folder.'
    )
    parser.add_argument('--client', required=True,
                        help='Client project folder (under the repo root) or an absolute '
                             'path to it, e.g. "INKtentions". Must contain a .env.')
    parser.add_argument('--days', type=int, default=7, help='Number of days to report on (default: 7)')
    parser.add_argument('--output', type=str, default=None, help='Output PDF path (default: <client>/reports/...)')
    args = parser.parse_args()

    # Resolve the client folder relative to the repo root (parent of this reporting/ dir).
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    client_dir = args.client if os.path.isabs(args.client) else os.path.join(repo_root, args.client)
    if not os.path.isdir(client_dir):
        parser.error(f'Client folder not found: {client_dir}')
    if not os.path.isfile(os.path.join(client_dir, '.env')):
        parser.error(f'No .env found in client folder: {client_dir}')

    configure_client(client_dir)
    if not TOKEN or not ACCOUNT_ID:
        parser.error(f'{args.client}/.env is missing META_ACCESS_TOKEN or META_AD_ACCOUNT_ID')

    if args.days <= 7:
        date_preset = 'last_7d'
    elif args.days <= 14:
        date_preset = 'last_14d'
    elif args.days <= 30:
        date_preset = 'last_30d'
    else:
        date_preset = 'last_90d'

    if not args.output:
        today_str = datetime.now().strftime('%Y-%m-%d')
        args.output = os.path.join(
            client_dir, 'reports',
            f'{CLIENT_NAME.lower().replace(" ", "-")}-report-{today_str}.pdf'
        )

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    print(f'Client: {CLIENT_NAME}  ({args.client})')

    print(f'Fetching data for last {args.days} days...')
    account_info = fetch_account_info()
    campaigns = fetch_campaign_insights(date_preset)
    adsets = fetch_adset_insights(date_preset)
    ads = fetch_ad_insights(date_preset)
    daily = fetch_daily_insights(args.days)
    image_data = fetch_image_breakdown(date_preset)
    age_gender_data = fetch_age_gender_breakdown(date_preset)
    platform_data = fetch_platform_breakdown(date_preset)
    body_data = fetch_body_breakdown(date_preset)
    title_data = fetch_title_breakdown(date_preset)
    desc_data = fetch_description_breakdown(date_preset)

    print(f'Found {len(campaigns)} campaigns, {len(adsets)} ad sets, {len(ads)} ads')
    print(f'Found {len(image_data)} image breakdowns, {len(age_gender_data)} age/gender rows, {len(platform_data)} placement rows')
    print(f'Found {len(body_data)} primary text variants, {len(title_data)} headlines, {len(desc_data)} descriptions')
    print(f'Generating PDF...')

    output = build_pdf(
        args.output, args.days, account_info, campaigns, adsets, ads, daily,
        image_data, age_gender_data, platform_data,
        body_data=body_data, title_data=title_data, desc_data=desc_data
    )
    print(f'Report saved: {output}')


if __name__ == '__main__':
    main()
