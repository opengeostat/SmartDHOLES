from django import template
register = template.Library()
@register.filter
def repl(value, arg):
    """Removes all values of arg from the given string"""
    return value.replace(arg, '_')
