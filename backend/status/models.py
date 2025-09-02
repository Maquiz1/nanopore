from django.db import models

class Status(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = "status"
        ordering = ["name"]

    def __str__(self):
        return self.name


class FormStatus(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = "form_status"
        ordering = ["name"]

    def __str__(self):
        return self.name
