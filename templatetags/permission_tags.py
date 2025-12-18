from django import template

register = template.Library()

@register.filter
def has_permission(user, perm):
    return user.has_perm(perm)




@register.filter
def kg_to_bags(value):
    """Convert kilograms to bags with proper rounding"""
    try:
        return round(float(value) / 62.5)
    except (ValueError, TypeError):
        return 0