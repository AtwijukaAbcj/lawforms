from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Get item from dictionary using a key."""
    if dictionary is None:
        return None
    # Handle 'pageX' format
    page_key = f"page{key}"
    return dictionary.get(page_key, dictionary.get(key))
