"""Custom template filters shared by the Admin recruitment monitoring pages."""
from django import template

register = template.Library()


@register.filter
def get_item(mapping, key):
    """Dictionary lookup with a variable key inside templates."""
    if mapping is None:
        return 0
    try:
        return mapping.get(key, 0)
    except AttributeError:
        return 0
