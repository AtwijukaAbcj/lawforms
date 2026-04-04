"""
Script to add value="{{ page_data.FIELDNAME|default:'' }}" to all input/textarea fields
in Form 13.1 templates that are missing it.
"""
import re
from pathlib import Path

templates_dir = Path("forms/templates/forms")

def add_value_to_inputs(content):
    """Add value attribute to input fields that have name= but no value="""
    
    # Pattern for input fields with name but no value
    # Match: <input ... name="field_name" ...> without value=
    def replace_input(match):
        tag = match.group(0)
        # Skip if already has value=
        if 'value=' in tag or 'value =' in tag:
            return tag
        # Skip hidden/submit/checkbox/radio
        type_match = re.search(r'type=["\'](\w+)["\']', tag, re.IGNORECASE)
        if type_match:
            input_type = type_match.group(1).lower()
            if input_type in ('hidden', 'submit', 'checkbox', 'radio', 'button'):
                return tag
        
        # Get field name
        name_match = re.search(r'name=["\']([^"\']+)["\']', tag)
        if not name_match:
            return tag
        field_name = name_match.group(1)
        
        # Skip csrf and nav buttons
        if field_name in ('csrfmiddlewaretoken', 'prev', 'next', 'save', 'submit'):
            return tag
        
        # Insert value= before the closing >
        # Handle self-closing tags
        if tag.rstrip().endswith('/>'):
            new_tag = tag.rstrip()[:-2] + f' value="{{{{ page_data.{field_name}|default:\'\' }}}}"' + '/>'
        else:
            new_tag = tag.rstrip()[:-1] + f' value="{{{{ page_data.{field_name}|default:\'\' }}}}">'
        return new_tag
    
    # Process input tags
    content = re.sub(r'<input\s[^>]*name=[^>]*>', replace_input, content, flags=re.IGNORECASE)
    
    # Process textarea tags - add content between tags
    def replace_textarea(match):
        tag_open = match.group(1)
        existing_content = match.group(2)
        
        # Get field name
        name_match = re.search(r'name=["\']([^"\']+)["\']', tag_open)
        if not name_match:
            return match.group(0)
        field_name = name_match.group(1)
        
        # If already has django template variable, skip
        if '{{' in existing_content or '{%' in existing_content:
            return match.group(0)
        
        # Replace with page_data value
        return f'{tag_open}{{{{ page_data.{field_name}|default:\'\' }}}}</textarea>'
    
    content = re.sub(
        r'(<textarea\s[^>]*name=[^>]*>)([\s\S]*?)</textarea>',
        replace_textarea,
        content,
        flags=re.IGNORECASE
    )
    
    return content


# Process all Form 13.1 page templates
for template_file in sorted(templates_dir.glob("financial_statement_131_page*.html")):
    print(f"Processing {template_file.name}...")
    
    content = template_file.read_text(encoding='utf-8')
    new_content = add_value_to_inputs(content)
    
    if content != new_content:
        template_file.write_text(new_content, encoding='utf-8')
        print(f"  Updated!")
    else:
        print(f"  No changes needed")

print("\nDone!")
