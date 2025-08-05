# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

# from phonenumber_field.modelfields import PhoneNumberField

# class CustomUser(AbstractUser):
#     phone_number = PhoneNumberField(null=True, blank=True, unique=True)
#     phone_verification_code = models.CharField(max_length=6, blank=True, null=True)
#     is_phone_verified = models.BooleanField(default=False)
