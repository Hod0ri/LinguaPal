"""
LRS Views Package

Contains views for:
- xAPI LRS standard endpoints (Statement API, About)
- cmi5 Launch and Session management
- Admin Dashboard analytics
"""

from .xapi import (
    StatementView,
    AboutView,
)
from .cmi5 import (
    CMI5LaunchView,
    CMI5SessionView,
    CMI5AuthTokenView,
)
from .dashboard import (
    DashboardOverviewView,
    DashboardUsersView,
    DashboardTrendsView,
    DashboardRealtimeView,
    StatementListView,
    LRSCredentialViewSet,
)

__all__ = [
    # xAPI
    'StatementView',
    'AboutView',
    # cmi5
    'CMI5LaunchView',
    'CMI5SessionView',
    'CMI5AuthTokenView',
    # Dashboard
    'DashboardOverviewView',
    'DashboardUsersView',
    'DashboardTrendsView',
    'DashboardRealtimeView',
    'StatementListView',
    'LRSCredentialViewSet',
]
