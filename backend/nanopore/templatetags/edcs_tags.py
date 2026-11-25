"""The View EDCS/TBLIS button on the Zonal Lab and CTRL forms."""
from django import template
from django.urls import reverse

from nanopore.models import EdcsTblisZonal
from nanopore.zonal_rules import viewable_edcs_records

register = template.Library()


@register.simple_tag
def edcs_link(zonal_lab, user):
    """{"url": ...} for the participant's EDCS/TBLIS record, {"missing": True} before it is built,
    None when there is no saved form or the user may not open EDCS/TBLIS records."""
    if not getattr(zonal_lab, "pk", None) or not user.is_authenticated:
        return None
    record = EdcsTblisZonal.objects.filter(screening_id=zonal_lab.screening_id).only("pk").first()
    viewable = viewable_edcs_records(user)
    if record is None:
        return {"missing": True} if viewable.query.is_empty() is False else None
    if not viewable.filter(pk=record.pk).exists():
        return None
    return {"url": reverse("nanopore:edcs-tblis-laboratory-view", args=[record.pk])}
