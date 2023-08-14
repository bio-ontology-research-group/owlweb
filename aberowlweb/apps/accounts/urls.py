from django.urls import include, path
from django.contrib.auth.decorators import login_required
from accounts.views import (
    ProfileDetailView, ProfileUpdateView)


urlpatterns = [
    path('profile/', login_required(
        ProfileDetailView.as_view()), name='profile'),
    path('profile/edit/', login_required(
        ProfileUpdateView.as_view()), name='profile_edit'),
    path('', include('allauth.account.urls')),
]
