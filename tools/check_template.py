import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "family_law.settings")
import django
django.setup()

from django.template import loader, TemplateSyntaxError

path = 'forms/comparison_nfp_page1.html'
try:
    tpl = loader.get_template(path)
    print('TEMPLATE OK:', path)
except TemplateSyntaxError as e:
    print('TEMPLATE SYNTAX ERROR:', e)
    raise
except Exception as e:
    print('TEMPLATE LOAD ERROR:', repr(e))
    raise
