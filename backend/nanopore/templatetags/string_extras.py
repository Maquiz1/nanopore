# nanopore/templatetags/string_extras.py
from django import template

register = template.Library()

@register.filter
def split(value, key):
    """Splits the string by the given key and returns a list"""
    if not value:
        return []
    return str(value).split(key)

@register.filter
def startswith(value, prefix):
    """Returns True if the string starts with the given prefix"""
    if not value:
        return False
    return str(value).startswith(prefix)
