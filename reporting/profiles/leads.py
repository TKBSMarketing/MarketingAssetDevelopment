"""
Lead-generation report profile.

Headlines leads, cost-per-lead, and landing-page views. Used when every
campaign in the report has the Leads objective and the pixel has tracked at
least one lead.
"""
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph

import metrics as M
from profiles.base import ReportProfile


class LeadsProfile(ReportProfile):
    objective = 'Leads'
    name = 'Leads'

    @classmethod
    def campaign_table(cls, campaigns, styles, usable_width):
        header = ['Campaign', 'Objective', 'Spend', 'Leads', 'Cost/Lead', 'LPVs', 'Link CTR', 'CPC (Link)']
        rows = [header]
        for c in campaigns:
            leads = M.extract_leads(c)
            cpl = M.extract_cost_per_lead(c)
            lpv = M.extract_landing_page_views(c)
            rows.append([
                Paragraph(c.get('campaign_name', 'Unknown'), styles['TableCell']),
                M.get_objective_label(c),
                M.fmt_money(c.get('spend', 0)),
                M.fmt_number(leads) if leads else '—',
                M.fmt_money(cpl) if cpl else '—',
                M.fmt_number(lpv),
                M.fmt_pct(M.calc_link_ctr(c)),
                M.fmt_money(M.calc_link_cpc(c)),
            ])
        widths = [(usable_width - 5.55*inch), 0.7*inch, 0.65*inch, 0.55*inch, 0.75*inch, 0.55*inch, 0.6*inch, 0.75*inch]
        return rows, widths

    @classmethod
    def daily_table(cls, daily, usable_width):
        header = ['Date', 'Spend', 'Impressions', 'Link Clicks', 'Leads', 'Link CTR', 'CPC (Link)']
        rows = [header]
        for d in sorted(daily, key=lambda x: x.get('date_start', '')):
            leads = M.extract_leads(d)
            rows.append([
                d.get('date_start', 'N/A'),
                M.fmt_money(d.get('spend', 0)),
                M.fmt_number(d.get('impressions', 0)),
                M.fmt_number(M.extract_link_clicks(d)),
                M.fmt_number(leads) if leads else '—',
                M.fmt_pct(M.calc_link_ctr(d)),
                M.fmt_money(M.calc_link_cpc(d)),
            ])
        widths = [(usable_width - 4.85*inch), 0.75*inch, 1.0*inch, 0.85*inch, 0.55*inch, 0.65*inch, 0.75*inch]
        return rows, widths
