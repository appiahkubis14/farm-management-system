from django import template

register = template.Library()

@register.filter
def kg_to_bags(value):
    """Convert kilograms to bags (1 bag = 62.5kg)"""
    try:
        return round(float(value) / 62.5)
    except (ValueError, TypeError):
        return 0.0
    
# register = template.Library()

# @register.filter
# def subtract(value, arg):
#     return value - arg