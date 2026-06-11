#!/usr/bin/env python3
"""Fix all financial_statement_page templates to use page_data instead of statement."""
import re
import os

os.chdir('c:\\Users\\ABCJ\\Desktop\\lawforms')

files = [
    'forms/templates/forms/financial_statement_page3.html',
    'forms/templates/forms/financial_statement_page4.html',
    'forms/templates/forms/financial_statement_page5.html',
    'forms/templates/forms/financial_statement_page6.html',
    'forms/templates/forms/financial_statement_page7.html',
    'forms/templates/forms/financial_statement_page8.html',
]

def fix_template(content):
    """Apply all replacement patterns."""
    
    # Pattern 1: {{ statement.FIELD|default:statement.FIELD|floatformat:N|... }}
    # This catches cases with statement twice
    content = re.sub(
        r'\{\{\s*statement\.([a-z_]+)\|default:statement\.\1\|floatformat:(\d)',
        r'{{ page_data.\1|default:statement.\1|floatformat:\2',
        content
    )
    
    # Pattern 2: {{ statement.FIELD|floatformat:N|default:'' }}
    content = re.sub(
        r'\{\{\s*statement\.([a-z_]+)\|floatformat:(\d)\|default:\'\'',
        r'{{ page_data.\1|default:statement.\1|floatformat:\2|default:\'\'',
        content
    )
    
    # Pattern 3: value="{{ statement.FIELD|floatformat:N|default:'' }}"
    content = re.sub(
        r'value="\{\{\s*statement\.([a-z_]+)\|floatformat:(\d)\|default:\'\'',
        r'value="{{ page_data.\1|default:statement.\1|floatformat:\2|default:\'\'',
        content
    )
    
    # Pattern 4: {{ statement.FIELD|default:'' }} (text fields)
    content = re.sub(
        r'\{\{\s*statement\.([a-z_]+)\|default:\'\'(?!\s*\|floatformat)',
        r'{{ page_data.\1|default:statement.\1|default:\'\'',
        content
    )
    
    # Pattern 5: value="{{ statement.FIELD|default:'' }}"
    content = re.sub(
        r'value="\{\{\s*statement\.([a-z_]+)\|default:\'\'',
        r'value="{{ page_data.\1|default:statement.\1|default:\'\'',
        content
    )
    
    # Pattern 6: {% if statement.FIELD %}...{% endif %} (checkboxes)
    content = re.sub(
        r'\{%\s*if\s+statement\.([a-z_]+)\s*%\}',
        r'{% if page_data.\1|default:statement.\1 %}',
        content
    )
    
    # Pattern 7: value="{{ statement.FIELD }}" (simple case)
    content = re.sub(
        r'value="\{\{\s*statement\.([a-z_]+)\s*\}\}"',
        r'value="{{ page_data.\1|default:statement.\1 }}"',
        content
    )
    
    return content

for fpath in files:
    print(f"Processing {fpath}...")
    
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Count changes
    orig = content.count('statement.')
    fixed_content = fix_template(content)
    after = fixed_content.count('statement.')
    
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print(f"  ✓ Fixed {fpath} (was {orig} statement. refs, now {after})")

print("\n✅ All templates updated successfully!")
