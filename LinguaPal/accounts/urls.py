from django.urls import path
from .views import (
    GoogleLoginView,
    GoogleConfigView,
    CurrentUserView,
    UserProfileView,
    LanguageListView,
    CountryListView
)


app_name = 'accounts'

urlpatterns = [
    # Authentication APIs (/api/v1/auth/*)
    path('auth/google/config', GoogleConfigView.as_view(), name='google_config'),
    path('auth/google/login', GoogleLoginView.as_view(), name='google_login'),

    # User APIs (/api/v1/users/*)
    path('users/me', CurrentUserView.as_view(), name='current_user'),
    path('users/me/profile', UserProfileView.as_view(), name='user_profile'),

    # Master Data APIs (/api/v1/master/*)
    path('master/languages', LanguageListView.as_view(), name='language_list'),
    path('master/countries', CountryListView.as_view(), name='country_list'),
]
