from django.urls import path,include
from django.contrib.auth import views as auth_views
from . import views

app_name = "users"

urlpatterns = [
    # Add this:
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    
    # Keep these:
    path("accounts/", include("django.contrib.auth.urls")),
    path("sign_up/", views.SignUpView.as_view(), name="sign_up"),
]
