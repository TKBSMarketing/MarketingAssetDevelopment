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
