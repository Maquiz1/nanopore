from django.db import models
    
class Sex(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Male, 2 for Female
    name = models.CharField(max_length=200, unique=True)  # e.g., "Male" or "Female"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_options_updated")

    class Meta:
        verbose_name = "Sex"
        verbose_name_plural = "Sex"
        ordering = ["id"]

    def __str__(self):
        return self.name
