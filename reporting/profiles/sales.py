"""
Sales / e-commerce report profile.

Headlines purchases, revenue, cost-per-purchase, and ROAS, and surfaces the
add-to-cart -> checkout -> purchase funnel. Used when every campaign in the
report has the Sales objective and the pixel has tracked at least one purchase.
"""
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph

import metrics as M
from profiles.base import ReportProfile


class SalesProfile(ReportProfile):
    objective = 'Sales'
    name = 'Sales'

    @classmethod
    def summary_cells(cls, totals, metric_cell):
        return [
            metric_cell('Purchases', M.fmt_number(totals['purchases'])),
            metric_cell('Revenue', M.fmt_money(totals['revenue'])),
            metric_cell('Cost / Purchase', M.fmt_money(totals['cost_per_purchase'])),
            metric_cell('ROAS', M.fmt_roas(totals['roas'])),
        ]

    @classmethod
    def exec_line(cls, stats, styles):
        if stats.get('purchases', 0) <= 0:
            return None
        roas = stats.get('roas', 0)
        roas_color = M.COLOR_GREEN if roas >= 2.0 else (M.COLOR_YELLOW if roas >= 1.0 else M.COLOR_RED)
        return Paragraph(
            f'<font color="{roas_color}" size="14">&#9679;</font> '
            f'<b>ROAS: {M.fmt_roas(roas)}</b> &nbsp;&nbsp; '
            f'Revenue: {M.fmt_money(stats["revenue"])} &nbsp;&nbsp; '
            f'Add to Cart: {M.fmt_number(stats["add_to_cart"])} &nbsp;&nbsp; '
            f'Checkouts: {M.fmt_number(stats["initiate_checkout"])}',
            styles['ExecMetric']
        )

    @classmethod
    def campaign_table(cls, campaigns, styles, usable_width):
        header = ['Campaign', 'Spend', 'Purchases', 'ATC', 'Revenue', 'ROAS', 'Link CTR', 'CPC (Link)']
        rows = [header]
        for c in campaigns:
            purchases = M.extract_purchases(c)
            atc = M.extract_add_to_cart(c)
            revenue = M.extract_purchase_value(c)
            rows.append([
                Paragraph(c.get('campaign_name', 'Unknown'), styles['TableCell']),
                M.fmt_money(c.get('spend', 0)),
                M.fmt_number(purchases) if purchases else '—',
                M.fmt_number(atc) if atc else '—',
                M.fmt_money(revenue) if revenue else '—',
                M.fmt_roas(M.calc_roas(c)) if revenue else '—',
                M.fmt_pct(M.calc_link_ctr(c)),
                M.fmt_money(M.calc_link_cpc(c)),
            ])
        widths = [(usable_width - 4.65*inch), 0.7*inch, 0.8*inch, 0.5*inch, 0.8*inch, 0.55*inch, 0.7*inch, 0.8*inch]
        return rows, widths

    @classmethod
    def daily_table(cls, daily, usable_width):
        header = ['Date', 'Spend', 'Impressions', 'Link Clicks', 'Purchases', 'Revenue', 'Link CTR', 'CPC (Link)']
        rows = [header]
        for d in sorted(daily, key=lambda x: x.get('date_start', '')):
            purchases = M.extract_purchases(d)
            revenue = M.extract_purchase_value(d)
            rows.append([
                d.get('date_start', 'N/A'),
                M.fmt_money(d.get('spend', 0)),
                M.fmt_number(d.get('impressions', 0)),
                M.fmt_number(M.extract_link_clicks(d)),
                M.fmt_number(purchases) if purchases else '—',
                M.fmt_money(revenue) if revenue else '—',
                M.fmt_pct(M.calc_link_ctr(d)),
                M.fmt_money(M.calc_link_cpc(d)),
            ])
        widths = [(usable_width - 5.3*inch), 0.7*inch, 0.95*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.7*inch, 0.75*inch]
        return rows, widths
