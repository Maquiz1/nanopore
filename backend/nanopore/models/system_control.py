from django.db import models

class SystemControl(models.Model):
    enable_form_submissions = models.BooleanField(
        default=True, 
        help_text="If unchecked, the 'Submit' button on all forms will be disabled."
    )
    enable_new_screening = models.BooleanField(
        default=True,
        help_text="If unchecked, the 'New Screening' button will be hidden from the dashboard."
    )
    zonal_lab_by_section = models.BooleanField(
        default=True,
        help_text="If checked, Zonal Lab records open section by section; if unchecked, as the single full form.",
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "System Control"
        verbose_name_plural = "System Controls"

    def __str__(self):
        return f"System Controls (Updated {self.updated_at.strftime('%Y-%m-%d %H:%M')})"
