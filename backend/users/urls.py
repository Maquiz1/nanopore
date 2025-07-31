from django.urls import path,include
from django.contrib.auth import views as auth_views
from .views import CustomLoginView,SignUpView, ActivateAccount,ResendActivationEmailView
from django.views.generic import TemplateView

app_name = 'users'

urlpatterns = [
    path('sign_up/', SignUpView.as_view(), name='sign_up'),
    path('activate/<uidb64>/<token>/', ActivateAccount.as_view(), name='activate_account'),
    path('email_confirmation_sent/', TemplateView.as_view(template_name='registration/email_confirmation_sent.html'), name='email_confirmation_sent'),
    path('resend-activation/', ResendActivationEmailView.as_view(), name='resend_activation'),

    path("accounts/", include("django.contrib.auth.urls")),

    # existing login/logout paths
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]

