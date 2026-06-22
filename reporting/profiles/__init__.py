"""
Report profiles, selected per campaign objective.

The engine calls select_profile(campaigns) to pick the layout for the report's
headline sections (summary grid, exec card, campaign table, daily trend), and
profile_for_objective(obj) to pick the right exec-summary highlight line for
each objective group within a mixed account.

Adding a new campaign type = add a file here with a ReportProfile subclass and
register it in _BY_OBJECTIVE. The shared engine does not change.
"""
import metrics as M
from profiles.base import ReportProfile
from profiles.sales import SalesProfile
from profiles.leads import LeadsProfile
from profiles.traffic import TrafficProfile

__all__ = [
    'ReportProfile', 'SalesProfile', 'LeadsProfile', 'TrafficProfile',
    'select_profile', 'profile_for_objective',
]

# Objective label -> profile class. Objectives not listed fall back to base.
_BY_OBJECTIVE = {
    'Sales': SalesProfile,
    'Leads': LeadsProfile,
    'Traffic': TrafficProfile,
    'Engagement': TrafficProfile,
    'Awareness': TrafficProfile,
}


def profile_for_objective(objective):
    """Profile for a single objective label (used per exec-summary group)."""
    return _BY_OBJECTIVE.get(objective, ReportProfile)


def select_profile(campaigns):
    """Pick the profile that drives the report's headline layout.

    A specialized profile (Sales/Leads) is used only when every campaign shares
    that objective AND the pixel has tracked the relevant conversion, so a
    single stray pixel event never flips the whole report. Mixed-objective
    accounts fall back to the generic link-click layout.
    """
    objectives = {M.get_objective_label(c) for c in campaigns}
    if objectives == {'Sales'} and any(M.extract_purchases(c) > 0 for c in campaigns):
        return SalesProfile
    if objectives == {'Leads'} and any(M.extract_leads(c) > 0 for c in campaigns):
        return LeadsProfile
    if len(objectives) == 1:
        return profile_for_objective(next(iter(objectives)))
    return ReportProfile
