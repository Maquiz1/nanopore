# aggregates / counts

from django.db.models import Q, Count
from .duplicates import get_duplicate_lab_numbers
from .filters import get_zonal_dq_filters

def get_zonal_stats(qs):
    duplicates = get_duplicate_lab_numbers(qs)
    
    dq_filters = get_zonal_dq_filters(qs.model)

    aggregates = {
        key: Count("id", filter=q_filter, distinct=True)
        for key, q_filter in dq_filters.items()
    }
    
    # Handle duplicate lab logic manually as before
    aggregates["duplicate_unique_lab_no"] = Count("id", filter=Q(unique_lab_no__in=duplicates), distinct=True)

    stats = qs.aggregate(**aggregates)
    total = sum(stats.values())

    return stats, total, duplicates
