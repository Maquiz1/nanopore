# mails.py

import django
import os

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.settings")
django.setup()

from django.core.mail import send_mail

send_mail(
    subject='Test Email from Django',
    message='This is a test email sent using SendGrid.',
    from_email='wmakwesheni@gmail.com',
    recipient_list=['manquiz92@gmail.com'],
)