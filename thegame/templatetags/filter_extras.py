from django import template

register = template.Library()

@register.filter
def full_add(value, arg):
    return float(value) + float(arg)
    
@register.filter
def full_subtract(value, arg):
    return float(value) - float(arg)
