from django import template

register = template.Library()

# @register.filter(name='add_class')
# def add_class(field, css_class):
#     """
#     Add a CSS class to a form field widget.
#     Usage: {{ form.field|add_class:"form-control" }}
#     """
#     return field.as_widget(attrs={"class": css_class})

from django import template
from django.forms import Select, DateInput, ModelMultipleChoiceField

register = template.Library()

@register.filter
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})

@register.filter
def yesno_select(field):
    """
    Convert a BooleanField or 0/1 field to Yes/No select
    """
    from django.forms import Select
    choices = ((True, "Yes"), (False, "No"))
    if hasattr(field.field, "choices") and field.field.choices:
        return field
    return field.as_widget(widget=Select(choices=choices))

@register.filter
def widget_type(field):
    """
    Returns the class name of the widget in a template-safe way
    """
    return field.field.widget.__class__.__name__


@register.filter(name='add_placeholder')
def add_placeholder(field, placeholder_text):
    """
    Add a placeholder to a form field widget.
    Usage: {{ form.field|add_placeholder:"Enter your name" }}
    """
    return field.as_widget(attrs={"placeholder": placeholder_text})
