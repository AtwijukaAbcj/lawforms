import re

files = [
    'forms/templates/forms/financial_statement_page3.html',
    'forms/templates/forms/financial_statement_page4.html',
    'forms/templates/forms/financial_statement_page5.html',
    'forms/templates/forms/financial_statement_page6.html',
    'forms/templates/forms/financial_statement_page7.html',
    'forms/templates/forms/financial_statement_page8.html',
]

for fpath in files:
    with open(fpath) as f:
        content = f.read()
    refs = content.count('statement.')
    page_data = content.count('page_data.')
    print(f'{fpath.split("/")[-1]}: {refs} statement. | {page_data} page_data.')
