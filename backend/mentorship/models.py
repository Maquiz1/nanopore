from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from clinical.models import Disease, Competence
from locations.models import Site
import logging
from django.utils.timezone import now


User = get_user_model()

class Mentorship(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Mentorship {self.id}"


# Optional: configure logger
logger = logging.getLogger(__name__)

class Visit(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    mentor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mentorships')
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Visit by {self.mentor} to {self.site} ({self.start_date} to {self.end_date})"

    def clean(self):
        if self.end_date < self.start_date:
            raise ValidationError("End date cannot be earlier than start date.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        self.create_visit_days()

    def create_visit_days(self):
        total_days = (self.end_date - self.start_date).days + 1
        skipped_dates = []

        new_days = []
        for i in range(total_days):
            day = self.start_date + timedelta(days=i)
            if not VisitDay.objects.filter(visit=self, date=day).exists():
                new_days.append(VisitDay(visit=self, date=day))
            else:
                skipped_dates.append(day)

        VisitDay.objects.bulk_create(new_days)

        # Logging skipped dates (if any)
        if skipped_dates:
            logger.warning(
                f"Skipped creation of VisitDay(s) for Visit ID {self.id} on existing date(s): "
                f"{', '.join(str(d) for d in skipped_dates)}"
            )


class VisitDay(models.Model):
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='days')
    date = models.DateField()

    class Meta:
        unique_together = ('visit', 'date')
        ordering = ['date']

    def __str__(self):
        return f"{self.date} for {self.visit}"
    
    def is_completed(self):
        assignments = self.assignments.all()
        if not assignments.exists():
            return False
        return all(a.is_self_assessed and a.is_mentor_graded for a in assignments)
    
    # def completion_status(self):
    #     total = self.assignments.count()
    #     if total == 0:
    #         return "No assignments"
    #     completed = self.assignments.filter(is_self_assessed=True, is_mentor_graded=True).count()
    #     return f"{completed} of {total} completed"


class AssignedCompetence(models.Model):
    visit_day = models.ForeignKey(VisitDay, on_delete=models.CASCADE, related_name='assignments')
    mentee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_competencies')
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE)
    competence = models.ForeignKey(Competence, on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='competences_assigned')
    is_completed = models.BooleanField(default=False)
    is_self_assessed = models.BooleanField(default=False)
    mentor_grade = models.CharField(max_length=20, blank=True, null=True)  # e.g. Excellent, Good, Fair
    mentee_self_grade = models.CharField(max_length=20, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    mentor_remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('visit_day', 'mentee', 'competence')

    def clean(self):
        if self.visit_day.visit.mentor == self.mentee:
            raise ValidationError("Mentor cannot assign competencies to themselves.")

        if self.mentor_grade and self.mentor_grade not in ['Excellent', 'Good', 'Fair', 'Poor']:
            raise ValidationError("Mentor grade must be one of: Excellent, Good, Fair, Poor.")

        if self.mentee_self_grade and self.mentee_self_grade not in ['Excellent', 'Good', 'Fair', 'Poor']:
            raise ValidationError("Mentee self-grade must be one of: Excellent, Good, Fair, Poor.")

    def __str__(self):
        return f"{self.mentee} - {self.competence} ({'Done' if self.is_completed else 'Pending'})"


