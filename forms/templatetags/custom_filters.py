import re

from django import template


register = template.Library()

@register.filter
def first_sentences_by_words(value, limit=450):
    if not value:
        return ""

    limit = int(limit)
    text = str(value).strip()

    sentences = re.split(r'(?<=[.!?])\s+', text)

    result = []
    count = 0

    for sentence in sentences:
        words = sentence.split()

        if count + len(words) > limit:
            break

        result.append(sentence)
        count += len(words)

    return "\n".join(result)


@register.filter
def remaining_sentences_by_words(value, limit=450):
    if not value:
        return ""

    limit = int(limit)
    text = str(value).strip()

    sentences = re.split(r'(?<=[.!?])\s+', text)

    result = []
    count = 0
    remaining_started = False

    for sentence in sentences:
        words = sentence.split()

        if not remaining_started and count + len(words) <= limit:
            count += len(words)
            continue

        remaining_started = True
        result.append(sentence)

    return "\n".join(result)

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary using a key."""
    if dictionary is None:
        return None
    # Handle 'pageX' format
    page_key = f"page{key}"
    return dictionary.get(page_key, dictionary.get(key))


@register.filter
def or_(value, arg):
    """Return the logical OR of value and arg."""
    return bool(value or arg)


@register.filter
def remaining_words(value, arg):
    """Return the words after the first arg words."""
    if value is None:
        return ""
    try:
        count = int(arg)
    except (TypeError, ValueError):
        return ""
    text = str(value).strip()
    if not text:
        return ""
    words = re.split(r"\s+", text)
    if len(words) <= count:
        return ""
    return " ".join(words[count:])


@register.filter
def splitlines_filter(value):
    """Split a string by newlines."""
    if value is None:
        return []
    return str(value).split('\n')


@register.filter
def split(value, arg):
    """Split a string by a separator."""
    if value is None:
        return []
    return str(value).split(arg)
