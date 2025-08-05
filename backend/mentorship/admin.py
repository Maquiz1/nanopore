from django.contrib import admin
from .models import Mentorship, Visit, VisitDay, AssignedCompetence

admin.site.register(Mentorship)  # Assuming you have a Mentorship model to register
admin.site.register(Visit)  # Assuming you have a Visit model to register
admin.site.register(VisitDay)  # Assuming you have a VisitDay model to register
admin.site.register(AssignedCompetence)  # Assuming you have a AssignedCompetence model to register

