from django.urls import path
from .views import (
    google_login,
    google_config,
    current_user,
    language_list,
    country_list,
    get_profile,
    create_profile,
    update_profile,
)


app_name = 'accounts'

urlpatterns = [
    # Authentication APIs (/api/v1/auth/*)
    path('auth/google/config', google_config, name='google_config'),
    path('auth/google/login', google_login, name='google_login'),

    # User APIs (/api/v1/users/*)
    path('users/me', current_user, name='current_user'),
    path('users/me/profile', get_profile, name='user_profile'),
    path('users/me/profile/create', create_profile, name='create_profile'),
    path('users/me/profile/update', update_profile, name='update_profile'),

    # Master Data APIs (/api/v1/master/*)
    path('master/languages', language_list, name='language_list'),
    path('master/countries', country_list, name='country_list'),
]
