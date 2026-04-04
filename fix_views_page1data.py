"""
Update views.py to pass page1_data to pages 2-33.
"""
import re

VIEWS_FILE = r"c:\Users\ABCJ\Desktop\lawforms\forms\views.py"

with open(VIEWS_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to match render calls for pages 2-33 that don't already have page1_data
# Match: render(request, "forms/financial_statement_131_pageN.html", {"pk": pk, "form": form, "page_data": page_data})
pattern = re.compile(
    r'(return render\(request, "forms/financial_statement_131_page(\d+)\.html", \{"pk": pk, "form": form, "page_data": page_data\})\)',
    re.MULTILINE
)

def replace_render(match):
    full_match = match.group(1)
    page_num = int(match.group(2))
    if page_num >= 2:
        # Add page1_data to context
        return full_match.replace(
            '"page_data": page_data}',
            '"page_data": page_data, "page1_data": form.get_page_data(1)}' 
        ) + ')'
    return match.group(0)

new_content = pattern.sub(replace_render, content)

# Count changes
old_count = len(pattern.findall(content))
new_count = content.count('"page1_data": form.get_page_data(1)')
changes = new_content.count('"page1_data": form.get_page_data(1)') - new_count

print(f"Found {old_count} render calls for pages 2-33")
print(f"Added page1_data to {changes} render calls")

with open(VIEWS_FILE, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Done!")
