import re

files = [
    'forms/templates/forms/financial_statement_page7.html',
    'forms/templates/forms/financial_statement_page8.html',
]

def fix_double_statement(content):
    """Fix the double statement references pattern."""
    # Match: value="{{ statement.FIELD|default:statement.FIELD|...
    content = re.sub(
        r'value="\{\{\s*statement\.([a-z_]+)\|default:statement\.\1',
        r'value="{{ page_data.\1|default:statement.\1',
        content
    )
    return content

for fpath in files:
    print(f"Fixing {fpath}...")
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    fixed = fix_double_statement(content)
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(fixed)
    print(f"  ✓ Fixed")

print("\n✅ Double statement patterns fixed!")
