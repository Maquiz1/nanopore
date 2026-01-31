# reports/templatetags/custom_tags.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Returns the value for a key in a dictionary."""
    if dictionary is None:
        return None
    return dictionary.get(key, None)
