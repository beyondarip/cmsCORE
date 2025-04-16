from django import template

register = template.Library()

@register.filter
def split_lines(text):
    if text:
        return text.split('\n')
    return []

@register.filter
def get_item(dictionary, key):
    if dictionary and key:
        return dictionary.get(key)
    return None 