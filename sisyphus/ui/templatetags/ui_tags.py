from django import template
from django.utils.safestring import mark_safe


register = template.Library()


@register.filter('safe_like')
def safe_like(value):
    value = value.replace('<p><br/></p>', '')
    return mark_safe(value)
