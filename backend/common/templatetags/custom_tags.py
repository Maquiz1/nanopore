# templatetags/utils.py
from django import template

register = template.Library()

@register.filter
def get_item(queryset, pk):
    try:
        return queryset.get(pk=pk).name
    except:
        return None
    
    
