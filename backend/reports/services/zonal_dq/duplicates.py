# duplicate lab numbers

from django.db.models import Count

def get_duplicate_lab_numbers(qs):
    """
    Return a list of unique_lab_no values that appear more than once.
    NOTE: .order_by() MUST be called before .values().annotate() to clear
    any existing ordering — Django otherwise includes ORDER BY fields in
    GROUP BY, making each row its own group (cnt always = 1).
    """
    return list(
        qs.order_by()                          # ← clear ordering first
          .exclude(unique_lab_no__isnull=True)
          .exclude(unique_lab_no="")
          .values("unique_lab_no")
          .annotate(cnt=Count("id"))
          .filter(cnt__gt=1)
          .values_list("unique_lab_no", flat=True)
    )