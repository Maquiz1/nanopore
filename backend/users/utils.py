from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

def send_activation_email(user, activation_url):
    subject = 'Activate Your Account'
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = user.email

    context = {
        'username': user.username,
        'activation_url': activation_url,
    }

    text_content = render_to_string('users/emails/activation_email.txt', context)
    html_content = render_to_string('users/emails/activation_email.html', context)

    email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    email.attach_alternative(html_content, "text/html")
    email.send()
