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

@register.filter(name='get')
def get(d, k):
    return d.get(k, None)

@register.filter()
def loopDict(itemDict, parent):
    table = None
    for key, item in itemDict.iteritems():
        table = '<a href="#" class="list-group-item">'+key+'<small class="text-muted pull-right">'+parent+'</small></a>'
        if 'requires' or 'updates' in item:
            table += '<div class="list-group" style="padding-left:20px;">'
        if "requires" in item:
            table += loopDict(item["requires"], "required from "+key)
        if "updates" in item:
            table += loopDict(item["updates"], "update for "+key)
        if 'requires' or 'updates' in item:
            table += '</div>'

    return table

@register.filter
def calcbattery(current_value, max_value):
    return int(float(current_value)/max_value*4)

@register.filter
def calcbatteryprecent(current_value, max_value):
    return int(float(current_value)/max_value*100)

@register.filter
def get_type(value):
    return type(value)