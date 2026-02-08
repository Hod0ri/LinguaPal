"""
LRS URL Configuration

URL patterns for:
- xAPI LRS standard endpoints
- cmi5 Launch and Session management
- Admin Dashboard analytics
- LRS Credential management
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    # xAPI
    StatementView,
    AboutView,
    # cmi5
    CMI5LaunchView,
    CMI5SessionView,
    CMI5AuthTokenView,
    # Dashboard
    DashboardOverviewView,
    DashboardUsersView,
    DashboardTrendsView,
    DashboardRealtimeView,
    StatementListView,
    ActivityListView,
    LRSCredentialViewSet,
    DifficultyAnalysisView,
    EngagementMetricsView,
    RetentionMetricsView,
    GrowthMetricsView,
    # User stats
    UserStreakRecommendationView,
)

app_name = 'lrs'

# Router for ViewSets
router = DefaultRouter()
router.register(r'credentials', LRSCredentialViewSet, basename='credentials')

# xAPI standard endpoints (nested under /xapi/)
xapi_patterns = [
    path('statements', StatementView.as_view(), name='xapi-statements'),
    path('statements/', StatementView.as_view(), name='xapi-statements-slash'),
    path('about', AboutView.as_view(), name='xapi-about'),
    path('about/', AboutView.as_view(), name='xapi-about-slash'),
]

# cmi5 endpoints (nested under /cmi5/)
cmi5_patterns = [
    path('launch', CMI5LaunchView.as_view(), name='cmi5-launch'),
    path('launch/', CMI5LaunchView.as_view(), name='cmi5-launch-slash'),
    path('auth-token', CMI5AuthTokenView.as_view(), name='cmi5-auth-token'),
    path('auth-token/', CMI5AuthTokenView.as_view(), name='cmi5-auth-token-slash'),
    path('session/start', CMI5SessionView.as_view(), {'action': 'start'}, name='cmi5-session-start'),
    path('session/start/', CMI5SessionView.as_view(), {'action': 'start'}, name='cmi5-session-start-slash'),
    path('session/<uuid:session_id>', CMI5SessionView.as_view(), name='cmi5-session-detail'),
    path('session/<uuid:session_id>/', CMI5SessionView.as_view(), name='cmi5-session-detail-slash'),
    path('session/<uuid:session_id>/initialize', CMI5SessionView.as_view(), {'action': 'initialize'}, name='cmi5-session-initialize'),
    path('session/<uuid:session_id>/initialize/', CMI5SessionView.as_view(), {'action': 'initialize'}, name='cmi5-session-initialize-slash'),
    path('session/<uuid:session_id>/terminate', CMI5SessionView.as_view(), {'action': 'terminate'}, name='cmi5-session-terminate'),
    path('session/<uuid:session_id>/terminate/', CMI5SessionView.as_view(), {'action': 'terminate'}, name='cmi5-session-terminate-slash'),
    path('session/<uuid:session_id>/abandon', CMI5SessionView.as_view(), {'action': 'abandon'}, name='cmi5-session-abandon'),
    path('session/<uuid:session_id>/abandon/', CMI5SessionView.as_view(), {'action': 'abandon'}, name='cmi5-session-abandon-slash'),
]

# Dashboard endpoints (nested under /dashboard/)
dashboard_patterns = [
    path('overview', DashboardOverviewView.as_view(), name='dashboard-overview'),
    path('overview/', DashboardOverviewView.as_view(), name='dashboard-overview-slash'),
    path('users', DashboardUsersView.as_view(), name='dashboard-users'),
    path('users/', DashboardUsersView.as_view(), name='dashboard-users-slash'),
    path('trends', DashboardTrendsView.as_view(), name='dashboard-trends'),
    path('trends/', DashboardTrendsView.as_view(), name='dashboard-trends-slash'),
    path('realtime', DashboardRealtimeView.as_view(), name='dashboard-realtime'),
    path('realtime/', DashboardRealtimeView.as_view(), name='dashboard-realtime-slash'),
    path('activities', ActivityListView.as_view(), name='dashboard-activities'),
    path('activities/', ActivityListView.as_view(), name='dashboard-activities-slash'),
    path('difficulty', DifficultyAnalysisView.as_view(), name='dashboard-difficulty'),
    path('difficulty/', DifficultyAnalysisView.as_view(), name='dashboard-difficulty-slash'),
    path('engagement', EngagementMetricsView.as_view(), name='dashboard-engagement'),
    path('engagement/', EngagementMetricsView.as_view(), name='dashboard-engagement-slash'),
    path('retention', RetentionMetricsView.as_view(), name='dashboard-retention'),
    path('retention/', RetentionMetricsView.as_view(), name='dashboard-retention-slash'),
    path('growth', GrowthMetricsView.as_view(), name='dashboard-growth'),
    path('growth/', GrowthMetricsView.as_view(), name='dashboard-growth-slash'),
]

# User endpoints (authenticated, non-admin)
user_patterns = [
    path('streak-recommendation', UserStreakRecommendationView.as_view(), name='user-streak-recommendation'),
    path('streak-recommendation/', UserStreakRecommendationView.as_view(), name='user-streak-recommendation-slash'),
]

urlpatterns = [
    # xAPI LRS endpoints
    path('xapi/', include(xapi_patterns)),

    # cmi5 endpoints
    path('cmi5/', include(cmi5_patterns)),

    # Dashboard endpoints
    path('dashboard/', include(dashboard_patterns)),

    # User stats endpoints
    path('user/', include(user_patterns)),

    # Statement list (admin)
    path('statements', StatementListView.as_view(), name='statement-list'),
    path('statements/', StatementListView.as_view(), name='statement-list-slash'),

    # Credential management (router)
    path('', include(router.urls)),
]
