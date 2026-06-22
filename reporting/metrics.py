"""
Shared metric helpers for the Meta ad report engine.

This is the single source of truth for pulling values out of Meta Insights
rows, formatting them, and classifying campaign objectives. Both the report
engine (generate_report.py) and the per-objective profiles (profiles/) import
from here, so a fix made here flows everywhere.
"""
import re
from reportlab.platypus import Paragraph


# ---------------------------------------------------------------------------
# Action extraction
# ---------------------------------------------------------------------------

def extract_action(row, action_type):
    """Extract a specific action count from the actions array."""
    for a in row.get('actions', []):
        if a['action_type'] == action_type:
            return int(a['value'])
    return 0


def extract_link_clicks(row):
    actions = row.get('actions', [])
    return int(next((a['value'] for a in actions if a['action_type'] == 'link_click'), 0))


def extract_cost_per_link_click(row):
    costs = row.get('cost_per_action_type', [])
    val = next((a['value'] for a in costs if a['action_type'] == 'link_click'), None)
    return float(val) if val else None


def extract_leads(row):
    """Lead conversions — tries multiple action types in priority order."""
    for action_type in ['lead', 'onsite_web_lead', 'offsite_conversion.fb_pixel_lead', 'offsite_conversion.fb_pixel_custom']:
        val = extract_action(row, action_type)
        if val > 0:
            return val
    return 0


def extract_cost_per_lead(row):
    """Cost per lead from cost_per_action_type."""
    for action_type in ['lead', 'onsite_web_lead', 'offsite_conversion.fb_pixel_lead', 'offsite_conversion.fb_pixel_custom']:
        for a in row.get('cost_per_action_type', []):
            if a['action_type'] == action_type:
                return float(a['value'])
    return 0


def extract_landing_page_views(row):
    return extract_action(row, 'landing_page_view')


def extract_post_engagements(row):
    return extract_action(row, 'post_engagement')


def extract_video_views(row):
    return extract_action(row, 'video_view')


def extract_purchases(row):
    """Purchase conversions — tries pixel/omni variants in priority order."""
    for action_type in ['purchase', 'omni_purchase', 'offsite_conversion.fb_pixel_purchase', 'onsite_web_purchase']:
        val = extract_action(row, action_type)
        if val > 0:
            return val
    return 0


def extract_add_to_cart(row):
    for action_type in ['add_to_cart', 'omni_add_to_cart', 'offsite_conversion.fb_pixel_add_to_cart']:
        val = extract_action(row, action_type)
        if val > 0:
            return val
    return 0


def extract_initiate_checkout(row):
    for action_type in ['initiate_checkout', 'omni_initiated_checkout', 'offsite_conversion.fb_pixel_initiate_checkout']:
        val = extract_action(row, action_type)
        if val > 0:
            return val
    return 0


def extract_purchase_value(row):
    """Total purchase conversion value (revenue) from the action_values array."""
    for action_type in ['purchase', 'omni_purchase', 'offsite_conversion.fb_pixel_purchase', 'onsite_web_purchase']:
        for a in row.get('action_values', []):
            if a.get('action_type') == action_type:
                try:
                    return float(a['value'])
                except (TypeError, ValueError, KeyError):
                    return 0.0
    return 0.0


# ---------------------------------------------------------------------------
# Derived metrics
# ---------------------------------------------------------------------------

def calc_link_cpc(row):
    """Cost per link click (spend / link clicks). More useful than Meta's CPC,
    which includes all click types."""
    spend = float(row.get('spend', 0))
    lc = extract_link_clicks(row)
    return (spend / lc) if lc > 0 else 0


def calc_link_ctr(row):
    """Link CTR = link clicks / impressions. Reconciles with Link Clicks and CPC (Link)."""
    impressions = int(row.get('impressions', 0))
    lc = extract_link_clicks(row)
    return (lc / impressions * 100) if impressions else 0.0


def calc_roas(row):
    """Return on ad spend = purchase value / spend."""
    spend = float(row.get('spend', 0))
    val = extract_purchase_value(row)
    return (val / spend) if spend > 0 else 0.0


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------

def fmt_money(val):
    return f'${float(val):,.2f}' if val else '$0.00'


def fmt_number(val):
    return f'{int(val):,}' if val else '0'


def fmt_pct(val):
    return f'{float(val):.2f}%' if val else '0.00%'


def fmt_roas(val):
    return f'{float(val):.2f}x' if val else '0.00x'


# ---------------------------------------------------------------------------
# Objective classification
# ---------------------------------------------------------------------------

OBJECTIVE_LABELS = {
    'OUTCOME_TRAFFIC': 'Traffic',
    'OUTCOME_LEADS': 'Leads',
    'OUTCOME_SALES': 'Sales',
    'OUTCOME_ENGAGEMENT': 'Engagement',
    'OUTCOME_AWARENESS': 'Awareness',
    'OUTCOME_APP_PROMOTION': 'App Promotion',
    'LINK_CLICKS': 'Traffic',
    'LEAD_GENERATION': 'Leads',
    'CONVERSIONS': 'Conversions',
    'POST_ENGAGEMENT': 'Engagement',
    'BRAND_AWARENESS': 'Awareness',
    'REACH': 'Reach',
    'VIDEO_VIEWS': 'Video Views',
    'MESSAGES': 'Messages',
}


def get_objective_label(campaign):
    raw = campaign.get('objective', '')
    return OBJECTIVE_LABELS.get(raw, raw.replace('OUTCOME_', '').replace('_', ' ').title() if raw else 'Unknown')


# Primary metric = the metric that DEFINES success for this objective.
# Secondary metrics provide supporting context but aren't the headline.
OBJECTIVE_METRICS = {
    'Traffic': {
        'primary': 'link_clicks',
        'primary_cost': 'cpc_link',
        'primary_label': 'Link Clicks',
        'primary_cost_label': 'CPC (Link)',
        'thresholds': {
            'ctr': (2.0, 1.0),             # >2% green, 1-2% yellow, <1% red (higher=better)
            'cpc_link': (0.50, 1.00),       # <$0.50 green, $0.50-$1.00 yellow, >$1.00 red (lower=better)
        }
    },
    'Leads': {
        'primary': 'landing_page_views',
        'primary_cost': 'cost_per_lpv',
        'primary_label': 'Landing Page Views',
        'primary_cost_label': 'Cost / Landing Page View',
        'thresholds': {
            'ctr': (1.5, 0.8),              # Lead ads have lower CTR — that's normal
            'cost_per_lpv': (3.00, 8.00),   # <$3 green, $3-$8 yellow, >$8 red (lower=better)
            'cpc_link': (2.00, 5.00),       # Secondary — leads CPC is naturally higher
        }
    },
    'Sales': {
        'primary': 'link_clicks',
        'primary_cost': 'cpc_link',
        'primary_label': 'Link Clicks',
        'primary_cost_label': 'CPC (Link)',
        'thresholds': {
            'ctr': (1.5, 0.8),
            'cpc_link': (1.50, 4.00),
            'cost_per_purchase': (15.00, 40.00),  # <$15 green, $15-$40 yellow (lower=better)
        }
    },
    'Engagement': {
        'primary': 'post_engagements',
        'primary_cost': 'cost_per_engagement',
        'primary_label': 'Engagements',
        'primary_cost_label': 'Cost / Engagement',
        'thresholds': {
            'ctr': (3.0, 1.5),
            'cost_per_engagement': (0.10, 0.30),
        }
    },
    'default': {
        'primary': 'link_clicks',
        'primary_cost': 'cpc_link',
        'primary_label': 'Link Clicks',
        'primary_cost_label': 'CPC (Link)',
        'thresholds': {
            'ctr': (2.0, 1.0),
            'cpc_link': (1.00, 3.00),
        }
    }
}

# Backward compat alias
METRIC_THRESHOLDS = {k: v['thresholds'] for k, v in OBJECTIVE_METRICS.items()}

COLOR_GREEN = '#22c55e'
COLOR_YELLOW = '#f59e0b'
COLOR_RED = '#ef4444'


def traffic_light(value, thresholds, mode='lower_is_better'):
    """Return a color hex based on traffic-light thresholds (green, yellow)."""
    green_threshold, yellow_threshold = thresholds
    if mode == 'lower_is_better':
        if value <= green_threshold:
            return COLOR_GREEN
        elif value <= yellow_threshold:
            return COLOR_YELLOW
        return COLOR_RED
    else:  # higher_is_better
        if value >= green_threshold:
            return COLOR_GREEN
        elif value >= yellow_threshold:
            return COLOR_YELLOW
        return COLOR_RED


def traffic_light_paragraph(value, formatted_value, thresholds, mode, label, styles):
    """Return a Paragraph with a colored circle indicator, label, and formatted value."""
    color = traffic_light(value, thresholds, mode)
    return Paragraph(
        f'<font color="{color}">&#9679;</font> {label}: <b>{formatted_value}</b>',
        styles['BodyText']
    )


def get_primary_metrics(campaigns):
    """Aggregate metrics grouped by objective. For Leads campaigns, upgrade from
    landing-page views to actual leads when pixel data is available; for Sales
    campaigns, upgrade from link clicks to purchases."""
    obj_data = {}
    for c in campaigns:
        obj = get_objective_label(c)
        if obj not in obj_data:
            obj_data[obj] = {
                'spend': 0, 'impressions': 0, 'clicks': 0,
                'link_clicks': 0, 'landing_page_views': 0,
                'leads': 0, 'post_engagements': 0, 'video_views': 0,
                'purchases': 0, 'add_to_cart': 0, 'initiate_checkout': 0,
                'revenue': 0.0, 'campaigns': []
            }
        d = obj_data[obj]
        d['spend'] += float(c.get('spend', 0))
        d['impressions'] += int(c.get('impressions', 0))
        d['clicks'] += int(c.get('clicks', 0))
        d['link_clicks'] += extract_link_clicks(c)
        d['landing_page_views'] += extract_landing_page_views(c)
        d['leads'] += extract_leads(c)
        d['post_engagements'] += extract_post_engagements(c)
        d['video_views'] += extract_video_views(c)
        d['purchases'] += extract_purchases(c)
        d['add_to_cart'] += extract_add_to_cart(c)
        d['initiate_checkout'] += extract_initiate_checkout(c)
        d['revenue'] += extract_purchase_value(c)
        d['campaigns'].append(c.get('campaign_name', 'Unknown'))

    for obj, d in obj_data.items():
        config = OBJECTIVE_METRICS.get(obj, OBJECTIVE_METRICS['default']).copy()

        # For Leads campaigns: upgrade to actual lead data when pixel is tracking
        if obj == 'Leads' and d['leads'] > 0:
            config['primary'] = 'leads'
            config['primary_cost'] = 'cost_per_lead'
            config['primary_label'] = 'Leads'
            config['primary_cost_label'] = 'Cost / Lead'
            config['thresholds'] = dict(config.get('thresholds', {}))
            config['thresholds']['cost_per_lead'] = (30.00, 75.00)  # Local services benchmark

        # For Sales campaigns: upgrade to actual purchase data when pixel is tracking
        if obj == 'Sales' and d['purchases'] > 0:
            config['primary'] = 'purchases'
            config['primary_cost'] = 'cost_per_purchase'
            config['primary_label'] = 'Purchases'
            config['primary_cost_label'] = 'Cost / Purchase'

        d['primary_count'] = d.get(config['primary'], d['link_clicks'])
        d['primary_cost'] = (d['spend'] / d['primary_count']) if d['primary_count'] > 0 else 0
        # Link CTR (link clicks / impressions) so it reconciles with Link Clicks & CPC (Link)
        d['ctr'] = (d['link_clicks'] / d['impressions'] * 100) if d['impressions'] else 0
        d['cpc_link'] = (d['spend'] / d['link_clicks']) if d['link_clicks'] else 0
        d['cost_per_lpv'] = (d['spend'] / d['landing_page_views']) if d['landing_page_views'] else 0
        d['cost_per_lead'] = (d['spend'] / d['leads']) if d['leads'] else 0
        d['cost_per_purchase'] = (d['spend'] / d['purchases']) if d['purchases'] else 0
        d['cost_per_engagement'] = (d['spend'] / d['post_engagements']) if d['post_engagements'] else 0
        d['roas'] = (d['revenue'] / d['spend']) if d['spend'] else 0
        d['config'] = config

    return obj_data


# ---------------------------------------------------------------------------
# String cleaners
# ---------------------------------------------------------------------------

def clean_image_name(name):
    """Remove _105 or similar numeric suffixes from image asset names."""
    if not name:
        return 'Unknown'
    return re.sub(r'_\d+$', '', name)


def clean_placement_name(platform, position):
    """Convert API placement identifiers to human-readable names."""
    platform_clean = (platform or '').replace('_', ' ').title()
    position_clean = (position or '').replace('_', ' ').title()
    if platform_clean and position_clean:
        return f'{platform_clean} {position_clean}'
    return platform_clean or position_clean or 'Unknown'


def truncate_text(text, max_len=60):
    if not text:
        return 'Unknown'
    text = text.replace('\n', ' ').strip()
    if len(text) <= max_len:
        return text
    return text[:max_len-3] + '...'
