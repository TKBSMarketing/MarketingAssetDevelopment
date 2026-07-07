"""
Base report profile.

A profile owns the objective-specific parts of a report: which extra headline
metrics to show, the executive-summary highlight line, and the column layouts
for the Campaign Performance and Daily Trend tables. Everything else (API
fetching, PDF scaffolding, demographics, placements, copy analysis) lives in
the shared engine and is identical across objectives.

The base profile implements the generic "Traffic"-style layout (link clicks,
link CTR, CPC). Sales and Leads subclass it and override only what differs.
"""
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph

import metrics as M


class ReportProfile:
    objective = 'default'
    name = 'Performance'

    # -- Headline metric grid: extra cells appended after the universal ones --
    @classmethod
    def summary_cells(cls, totals, metric_cell):
        """Return a list of metric_cell(label, value) for the summary grid.
        Base profile adds nothing beyond the universal spend/clicks/CTR cells."""
        return []

    # -- Executive-summary highlight line for one objective group --
    @classmethod
    def exec_line(cls, stats, styles):
        """Return an optional extra Paragraph for the exec card, or None."""
        return None

    # -- Campaign Performance table: (rows_including_header, col_widths) --
    @classmethod
    def campaign_table(cls, campaigns, styles, usable_width):
        # Even on a mixed / non-sales account, surface conversions whenever any
        # campaign has them — purchases/revenue/ROAS are the money-in-vs-out
        # story and shouldn't be hidden just because objectives are mixed.
        has_purchases = any(M.extract_purchases(c) > 0 for c in campaigns)
        has_leads = any(M.extract_leads(c) > 0 for c in campaigns)

        if has_purchases:
            header = ['Campaign', 'Objective', 'Spend', 'Purchases', 'Revenue', 'ROAS', 'Link CTR', 'CPC (Link)']
            rows = [header]
            for c in campaigns:
                purchases = M.extract_purchases(c)
                revenue = M.extract_purchase_value(c)
                rows.append([
                    Paragraph(c.get('campaign_name', 'Unknown'), styles['TableCell']),
                    M.get_objective_label(c),
                    M.fmt_money(c.get('spend', 0)),
                    M.fmt_number(purchases) if purchases else '—',
                    M.fmt_money(revenue) if revenue else '—',
                    M.fmt_roas(M.calc_roas(c)) if revenue else '—',
                    M.fmt_pct(M.calc_link_ctr(c)),
                    M.fmt_money(M.calc_link_cpc(c)),
                ])
            widths = [(usable_width - 4.82*inch), 0.68*inch, 0.7*inch, 0.75*inch, 0.8*inch, 0.55*inch, 0.62*inch, 0.72*inch]
            return rows, widths

        if has_leads:
            header = ['Campaign', 'Objective', 'Spend', 'Leads', 'Cost/Lead', 'Link CTR', 'CPC (Link)']
            rows = [header]
            for c in campaigns:
                leads = M.extract_leads(c)
                cpl = M.extract_cost_per_lead(c)
                rows.append([
                    Paragraph(c.get('campaign_name', 'Unknown'), styles['TableCell']),
                    M.get_objective_label(c),
                    M.fmt_money(c.get('spend', 0)),
                    M.fmt_number(leads) if leads else '—',
                    M.fmt_money(cpl) if cpl else '—',
                    M.fmt_pct(M.calc_link_ctr(c)),
                    M.fmt_money(M.calc_link_cpc(c)),
                ])
            widths = [(usable_width - 4.05*inch), 0.75*inch, 0.7*inch, 0.6*inch, 0.75*inch, 0.6*inch, 0.65*inch]
            return rows, widths

        # No conversions tracked anywhere: link-click layout with Reach.
        header = ['Campaign', 'Objective', 'Spend', 'Reach', 'Link Clicks', 'Link CTR', 'CPC (Link)']
        rows = [header]
        for c in campaigns:
            rows.append([
                Paragraph(c.get('campaign_name', 'Unknown'), styles['TableCell']),
                M.get_objective_label(c),
                M.fmt_money(c.get('spend', 0)),
                M.fmt_number(c.get('reach', 0)),
                M.fmt_number(M.extract_link_clicks(c)),
                M.fmt_pct(M.calc_link_ctr(c)),
                M.fmt_money(M.calc_link_cpc(c)),
            ])
        widths = [(usable_width - 4.85*inch), 0.8*inch, 0.7*inch, 0.7*inch, 0.85*inch, 0.65*inch, 0.85*inch]
        return rows, widths

    # -- Daily Trend table: (rows_including_header, col_widths) --
    @classmethod
    def daily_table(cls, daily, usable_width):
        header = ['Date', 'Spend', 'Impressions', 'Link Clicks', 'Link CTR', 'CPC (Link)']
        rows = [header]
        for d in sorted(daily, key=lambda x: x.get('date_start', '')):
            rows.append([
                d.get('date_start', 'N/A'),
                M.fmt_money(d.get('spend', 0)),
                M.fmt_number(d.get('impressions', 0)),
                M.fmt_number(M.extract_link_clicks(d)),
                M.fmt_pct(M.calc_link_ctr(d)),
                M.fmt_money(M.calc_link_cpc(d)),
            ])
        widths = [(usable_width - 4.2*inch), 0.8*inch, 1.1*inch, 0.9*inch, 0.7*inch, 0.7*inch]
        return rows, widths
