from django.urls import path
from .views import GoogleLoginView, GoogleConfigView, CurrentUserView


app_name = 'accounts'

urlpatterns = [
    path('google/config/', GoogleConfigView.as_view(), name='google_config'),
    path('google/login/', GoogleLoginView.as_view(), name='google_login'),
    path('me/', CurrentUserView.as_view(), name='current_user'),
]
