# users/models.py
from django.db import models
from django.contrib.auth import get_user_model
from phonenumber_field.modelfields import PhoneNumberField
from locations.models import Site, Zone

User = get_user_model()

class Prefix(models.Model):
    name = models.CharField(max_length=10, unique=True)  # e.g., Dr, PhD, Prof

    def __str__(self):
        return self.name


class Position(models.Model):
    name = models.CharField(max_length=50, unique=True)  # e.g., Researcher, Clinician

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    sites = models.ManyToManyField(Site, blank=True, related_name="profiles")
    zones = models.ManyToManyField(Zone, blank=True, related_name="profiles")
    phone_number = PhoneNumberField(null=True, blank=True, unique=True)
    prefix = models.ForeignKey(Prefix, on_delete=models.SET_NULL, null=True, blank=True)
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True)


    # NEW FIELDS
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        display_name = f"{self.prefix.name + ' ' if self.prefix else ''}{self.user.username}"
        return f"{display_name} - {self.position.name if self.position else 'No Position'}"
