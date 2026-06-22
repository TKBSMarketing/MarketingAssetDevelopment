"""
Traffic / engagement / awareness report profile.

This is the generic link-click layout (link clicks, link CTR, CPC). It is
identical to the base profile — defined here as a named profile so the engine
can map the Traffic/Engagement/Awareness objectives to an explicit class and so
the layout has an obvious home to diverge later if those objectives need it.
"""
from profiles.base import ReportProfile


class TrafficProfile(ReportProfile):
    objective = 'Traffic'
    name = 'Traffic'
