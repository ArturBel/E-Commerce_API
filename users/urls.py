from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path(route='register/', view=views.register, name='Registration'),
    path(route='login/', view=views.login, name='Login'),
    path(route='refresh/', view=TokenRefreshView.as_view(), name='Refresh endpoint'),
    path(route='edit/', view=views.edit_profile, name='Edit profile'),
    path(route='password/', view=views.password_reset, name='Password reset')
]