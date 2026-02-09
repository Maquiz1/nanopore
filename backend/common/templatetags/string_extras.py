# # common/templatetags/string_extras.py
# from django import template

# register = template.Library()

# @register.filter
# def startswith(text, starts):
#     if isinstance(text, str):
#         return text.startswith(starts)
#     return False


# # nanopore/templatetags/string_extras.py
# from django import template

# register = template.Library()

# @register.filter
# def split(value, key):
#     """Splits the string by the given key and returns a list"""
#     if not value:
#         return []
#     return str(value).split(key)

# @register.filter
# def startswith(value, prefix):
#     """Returns True if the string starts with the given prefix"""
#     if not value:
#         return False
#     return str(value).startswith(prefix)


from django import template

register = template.Library()

# -----------------------------
# Dictionary / List helpers
# -----------------------------

# @register.filter
# def get_item(dictionary, key):
#     """Returns the value for a key in a dictionary or None if missing."""
#     if dictionary is None:
#         return None
#     return dictionary.get(key, None)


# -----------------------------
# String helpers
# -----------------------------

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

@register.filter
def endswith(value, suffix):
    """Returns True if the string ends with the given suffix"""
    if not value:
        return False
    return str(value).endswith(suffix)

@register.filter
def contains(value, substring):
    """Returns True if the substring is in the string"""
    if not value:
        return False
    return str(substring) in str(value)


# -----------------------------
# Numeric / Misc helpers
# -----------------------------

@register.filter
def default_if_none(value, default=""):
    """Returns default if value is None"""
    if value is None:
        return default
    return value
