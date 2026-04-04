import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_law.settings')
django.setup()

from forms.views import _get_form131_template_meta, _build_form131_page_display_data

meta = _get_form131_template_meta()
print("Verifying page_header in built display data:")
for n in [1, 2, 15, 33]:
    page_meta = meta.get(n, {})
    display = _build_form131_page_display_data(
        n, {}, 
        page_meta.get("fields", []),
        "",
        page_meta.get("header", ""),
        page_meta.get("subheader", ""),
    )
    print(f"Page {n}:")
    print(f"  page_header: {display.get('page_header', '(missing)')[:60]}...")
    print(f"  page_subheader: {display.get('page_subheader', '(missing)')[:60]}...")
    print()
