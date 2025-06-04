# In your templatetags/wqi_tags.py
from django import template

register = template.Library()

@register.filter
def wqi_status(wqi):
    if wqi >= 90: return 'Excellent'
    if wqi >= 70: return 'Good'
    if wqi >= 50: return 'Medium'
    if wqi >= 25: return 'Poor'
    return 'Very Poor'

@register.filter
def wqi_status_class(wqi):
    if wqi >= 90: return 'bg-success'
    if wqi >= 70: return 'bg-primary'
    if wqi >= 50: return 'bg-warning'
    if wqi >= 25: return 'bg-danger'
    return 'bg-dark'