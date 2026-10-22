# utils/permissions.py
from utils.access import scope_queryset


def filter_queryset_by_user_role(user, qs, site_field="site"):
    """
    Limit qs to the records the user may see, based on their site/zone assignment.
    See utils/access.py for the rules.
    """
    if not hasattr(user, "is_superuser"):
        raise TypeError(f"Expected a single User object, got {type(user)}")
    return scope_queryset(user, qs, site_field=site_field)
