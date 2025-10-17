from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from django.urls import reverse_lazy, reverse
from .views import force_logout

from .views import (
    CustomLoginView,
    ProfileUpdateView,
    SignUpView,
    ActivateAccount,
    ResendActivationEmailView,
    StaffDetailView,
    StaffListView,
    VerifyPhoneView,
    SendPhoneVerificationView,
)

from users.forms import CustomPasswordResetForm

app_name = 'users'

urlpatterns = [
    path('profile/edit/', ProfileUpdateView.as_view(), name='edit-profile'),

    # Staff listing
    path('staff/', StaffListView.as_view(), name='staff_list'),
    path('staff/<int:pk>/', StaffDetailView.as_view(), name='staff_detail'),  # ✅ detail view
    
    # Registration and Activation
    path('sign_up/', SignUpView.as_view(), name='sign_up'),
    path('activate/<uidb64>/<token>/', ActivateAccount.as_view(), name='activate_account'),
    path('email_confirmation_sent/', TemplateView.as_view(
        template_name='registration/email_confirmation_sent.html'), name='email_confirmation_sent'),
    path('resend-activation/', ResendActivationEmailView.as_view(), name='resend_activation'),

    # Login and Logout
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    # path('logout/', auth_views.LogoutView.as_view(next_page='users:login'), name='logout'),# Redirect to login after logout

    # Password Reset
    path('accounts/password_reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        form_class=CustomPasswordResetForm,
        success_url=reverse_lazy('users:password_reset_done'),
        email_template_name='registration/password_reset_email.txt',  # ✅ Plain text version
        html_email_template_name='registration/password_reset_email.html',  # ✅ HTML version
        subject_template_name='registration/password_reset_subject.txt',  # ✅ Optional
    ), name='password_reset'),

    

    path('accounts/password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),

    path(
        'accounts/reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='registration/password_reset_confirm.html',
            success_url=reverse_lazy('users:password_reset_complete'),  # Adjust 'users' to your app namespace
        ),
        name='password_reset_confirm'
    ),
    path(
        'accounts/reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='registration/password_reset_complete.html',
        ),
        name='password_reset_complete'
    ),
    
    path('send-phone-verification/', SendPhoneVerificationView.as_view(), name='send_phone_verification'),
    path('verify-phone/', VerifyPhoneView.as_view(), name='verify_phone'),

    path('force-logout/', force_logout, name='force_logout'),
    
    path('session-expired/', TemplateView.as_view(
    template_name='registration/session_expired.html'), name='session_expired'),


]
