from django.db import models
from django.contrib.auth.models import User

class Household(models.Model):
    household_head_name = models.CharField(max_length=100)
    number_of_men = models.PositiveIntegerField()
    number_of_women = models.PositiveIntegerField()
    household_head_phone_number = models.CharField(max_length=15)
    veo = models.ForeignKey(User, on_delete=models.CASCADE)  # link to logged-in user

    @property
    def total_members(self):
        return self.number_of_men + self.number_of_women

    def __str__(self):
        return f"{self.household_head_name} - {self.veo.username}"
