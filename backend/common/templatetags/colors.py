# utils/templatetags/colors.py
from django import template

register = template.Library()

@register.filter
def perc_color(actual, target):
    """
    Returns a bootstrap class based on actual vs target percentage.
    Red <50%, Yellow 50-79%, Green >=80%
    """
    if not target or target == 0:
        return ''
    perc = actual / target
    if perc < 0.5:
        return 'bg-danger text-white'
    elif perc < 0.8:
        return 'bg-warning'
    else:
        return 'bg-success text-white'