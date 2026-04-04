"""
Update pages 2-33 to show full court header with read-only values from page 1.
"""
import os
import re

TEMPLATE_DIR = r"c:\Users\ABCJ\Desktop\lawforms\forms\templates\forms"

# The new full header for pages 2-33 (read-only court details from page1_data)
NEW_HEADER_TEMPLATE = '''<!-- Header Section -->
<div class="form-header-131">
  <div style="flex: 1;">
    <div class="form-title-green">MySupportCalculator.ca</div>
    <div style="margin-top: 14px;">
      <div style="text-align: center; font-weight: bold; font-size: 15px; margin-bottom: 8px;">ONTARIO</div>
      <div style="margin-bottom: 10px;">
        <div class="readonly-value {% if not page1_data.court_name %}empty{% endif %}">{{ page1_data.court_name|default:"—" }}</div>
        <div class="input-hint">(Name of court)</div>
      </div>
      <div style="display: flex; align-items: center; gap: 8px;">
        <span style="font-size: 14px;">at</span>
        <div style="flex: 1;">
          <div class="readonly-value {% if not page1_data.court_location %}empty{% endif %}">{{ page1_data.court_location|default:"—" }}</div>
          <div class="input-hint">(Court office address)</div>
        </div>
      </div>
    </div>
  </div>
  <div style="text-align: right; margin-left: 20px;">
    <div style="margin-bottom: 8px;">
      <div style="font-weight: 700; font-size: 12px; margin-bottom: 4px;">Court File Number</div>
      <div class="readonly-value mono {% if not page1_data.court_file_number %}empty{% endif %}">{{ page1_data.court_file_number|default:"—" }}</div>
    </div>
    <div class="form-badge-131">
      Form 13.1: Financial<br>Statement (Property and<br>Support Claims)<br>
      <span style="font-weight: normal;">sworn/affirmed</span>
    </div>
  </div>
</div>'''

# Pattern to match the existing header section in pages 2-33
# These have a simpler header structure
HEADER_PATTERN = re.compile(
    r'<!-- Header Section -->\s*<div class="form-header-131">.*?</div>\s*</div>',
    re.DOTALL
)

# Alternative pattern for headers without the comment
ALT_HEADER_PATTERN = re.compile(
    r'<div class="form-header-131">\s*<div>\s*<div class="form-title-green">.*?</div>\s*</div>\s*</div>',
    re.DOTALL
)

def update_template(page_num):
    filepath = os.path.join(TEMPLATE_DIR, f"financial_statement_131_page{page_num}.html")
    if not os.path.exists(filepath):
        print(f"  Page {page_num}: MISSING")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already has the full header (ONTARIO text)
    if 'ONTARIO</div>' in content and 'readonly-value' in content[:2000]:
        print(f"  Page {page_num}: Already updated")
        return True
    
    # Try to find and replace the header
    if HEADER_PATTERN.search(content):
        new_content = HEADER_PATTERN.sub(NEW_HEADER_TEMPLATE, content, count=1)
    elif ALT_HEADER_PATTERN.search(content):
        new_content = ALT_HEADER_PATTERN.sub(NEW_HEADER_TEMPLATE, content, count=1)
    else:
        # Manual search for the form-header-131 div
        start = content.find('<div class="form-header-131">')
        if start == -1:
            print(f"  Page {page_num}: No header found")
            return False
        
        # Find the closing - need to match nested divs
        depth = 0
        end = start
        i = start
        while i < len(content):
            if content[i:i+4] == '<div':
                depth += 1
                i += 4
            elif content[i:i+6] == '</div>':
                depth -= 1
                i += 6
                if depth == 0:
                    end = i
                    break
            else:
                i += 1
        
        if end <= start:
            print(f"  Page {page_num}: Could not find header end")
            return False
        
        # Also capture any comment before
        comment_start = start
        check_pos = start - 1
        while check_pos >= 0 and content[check_pos] in ' \t\n\r':
            check_pos -= 1
        if check_pos >= 22 and content[check_pos-22:check_pos+1].strip().endswith('-->'):
            # Find start of comment
            comment_search = content.rfind('<!--', 0, check_pos)
            if comment_search != -1 and 'Header' in content[comment_search:check_pos]:
                comment_start = comment_search
        
        old_header = content[comment_start:end]
        new_content = content[:comment_start] + NEW_HEADER_TEMPLATE + content[end:]
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"  Page {page_num}: Updated")
    return True

def main():
    print("Updating pages 2-33 with full read-only header...")
    success = 0
    for page in range(2, 34):
        if update_template(page):
            success += 1
    print(f"\nDone: {success}/32 templates updated")

if __name__ == "__main__":
    main()
