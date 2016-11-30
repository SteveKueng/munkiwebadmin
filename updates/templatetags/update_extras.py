from django import template

register = template.Library()

@register.filter
def humanreadablesize(bytes):
    """Returns sizes in human-readable units. Input is bytes"""
    try:
        bytes = float(bytes)
    except (TypeError, ValueError, UnicodeDecodeError):
        return "unknown"
        
    units = [(" B", 2**10), (" KB", 2**20), (" MB", 2**30), (" GB", 2**40), (" TB", 2**50)]
    for suffix, limit in units:
        if bytes > limit:
            continue
        else:
            return str(round(bytes/float(limit/2**10), 1)) + suffix
humanreadablesize.is_safe = True