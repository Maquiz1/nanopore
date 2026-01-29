from django import template

register = template.Library()

@register.filter(name='format_field')
def format_field(value):
    """
    Converts field names like 'missing_date_sputum_received' to 'Date Sputum Received'
    """
    if not isinstance(value, str):
        return value
    # remove "missing_" prefix
    value = value.replace("missing_", "")
    # replace underscores with spaces
    value = value.replace("_", " ")
    # capitalize each word
    return value.title()
