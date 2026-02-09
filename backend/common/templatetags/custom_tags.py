from django import template

register = template.Library()

@register.filter
def get_item(queryset_or_dict, key):
    """Returns value from queryset by pk or from dict by key."""
    if queryset_or_dict is None:
        return None

    try:
        # Try queryset
        return queryset_or_dict.get(pk=key).name
    except:
        # Try dictionary
        return queryset_or_dict.get(key, None)
