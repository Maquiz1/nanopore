from django.core.exceptions import ValidationError
from django.db import models

class UserManual(models.Model):
    title = models.CharField(max_length=255, unique=True)
    file = models.FileField(upload_to='manuals/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def clean(self):
        if UserManual.objects.exclude(pk=self.pk).filter(title__iexact=self.title).exists():
            raise ValidationError({'title': 'A manual with this title already exists.'})
