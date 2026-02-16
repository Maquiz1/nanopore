# duplicate lab numbers

from django.db.models import Count

def get_duplicate_lab_numbers(qs):
    return (
        qs.exclude(unique_lab_no__isnull=True)
          .exclude(unique_lab_no="")
          .values("unique_lab_no")
          .annotate(cnt=Count("id"))
          .filter(cnt__gt=1)
          .values_list("unique_lab_no", flat=True)
    )