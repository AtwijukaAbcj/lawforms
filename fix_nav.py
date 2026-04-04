"""
Script to update all Form 13.1 page templates to use the reusable navigation include.
"""
import re
from pathlib import Path

templates_dir = Path("forms/templates/forms")

# Pattern to match the old page-nav div including its style block
nav_pattern = re.compile(
    r'<style>\s*\.page-nav\{[^<]*?</style>\s*'  # style block
    r'(?:<!--[^>]*?-->\s*)?'  # optional comment
    r'<div class="page-nav">[\s\S]*?</div>',  # nav div
    re.IGNORECASE
)

# Alternative simpler pattern for just the nav div
nav_div_pattern = re.compile(
    r'<div class="page-nav">[\s\S]*?</div>',
    re.IGNORECASE
)

for i in range(1, 34):
    template_file = templates_dir / f"financial_statement_131_page{i}.html"
    if not template_file.exists():
        print(f"Page {i}: Template not found")
        continue
    
    content = template_file.read_text(encoding='utf-8')
    
    # Check if already using include
    if "financial_statement_131_nav.html" in content:
        print(f"Page {i}: Already using include")
        continue
    
    # Try to find and replace the navigation
    new_include = f"{{% include 'forms/financial_statement_131_nav.html' with current_page={i} pk=pk %}}"
    
    # First try full pattern with style
    if nav_pattern.search(content):
        new_content = nav_pattern.sub(new_include, content, count=1)
        template_file.write_text(new_content, encoding='utf-8')
        print(f"Page {i}: Updated (full pattern)")
    elif nav_div_pattern.search(content):
        # Just replace the nav div, keep style separate
        new_content = nav_div_pattern.sub(new_include, content, count=1)
        # Also try to remove orphaned page-nav style
        new_content = re.sub(
            r'<style>\s*\.page-nav\{[^<]*?</style>\s*',
            '',
            new_content,
            flags=re.IGNORECASE
        )
        template_file.write_text(new_content, encoding='utf-8')
        print(f"Page {i}: Updated (div only)")
    else:
        print(f"Page {i}: No navigation found to replace")

print("\nDone!")
