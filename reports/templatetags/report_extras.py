from django import template

register = template.Library()

@register.filter
def humanreadablesize(kbytes):
    """Returns sizes in human-readable units. Input is kbytes"""
    try:
        kbytes = float(kbytes)
    except (TypeError, ValueError, UnicodeDecodeError):
        return "unknown"
        
    units = [(" KB", 2**10), (" MB", 2**20), (" GB", 2**30), (" TB", 2**40)]
    for suffix, limit in units:
        if kbytes > limit:
            continue
        else:
            return str(round(kbytes/float(limit/2**10), 1)) + suffix
humanreadablesize.is_safe = True

@register.filter
def replace(value):
    value = value.replace ("_", " ")
    value = value.title()
    return value

@register.filter
def access_name(value, arg):
    return value[arg].display_name

@register.filter
def access_version(value, arg):
    return value[arg].version

@register.filter
def access_size(value, arg):
    size = humanreadablesize(value[arg].installer_item_size)
    return size

@register.filter
def access_icon(value, arg):
    return value[arg].icon_name

@register.filter(name='get')
def get(d, k):
    return d.get(k, None)