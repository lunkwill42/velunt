from django import template

register = template.Library()


@register.filter
def dictget(d, key):
    """Get a value from a dict by key. Returns None if missing."""
    if isinstance(d, dict):
        return d.get(key)
    return None


@register.filter
def numformat(value):
    """Format a Decimal/number as a plain numeric string for HTML attributes."""
    if value is None:
        return ""
    return f"{float(value):g}"


@register.simple_tag
def dim_integer_steps(dim):
    """Return the number of integer intervals in a dimension's range."""
    return int(dim.max_value - dim.min_value)
