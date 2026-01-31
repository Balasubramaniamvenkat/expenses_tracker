"""Test script for refined categorization"""

from SRC.refined_categories import RefinedCategorizer

cat = RefinedCategorizer()

tests = [
    ('UPI/123456/LAKSHMI', -5000),
    ('NEFT/REF123/TO LAKSHMI', -10000),
    ('UPI/123456/GRT JEWELLERS', -50000),
    ('NEFT/123/BHIMA JEWELLERS', -30000),
    ('UPI/123/TANISHQ', -25000),
    ('IMPS/123/RAVI KUMAR', -5000),
    ('UPI/123/APOLLO HOSPITAL', -3000),
    ('NEFT/123/ZERODHA', -10000),
    ('UPI/123/LIC OF INDIA', -5000),
    ('NEFT/123/THYROCARE', -2000),
    ('UPI/123/BYJUS', -5000),
]

print('Testing refined categorization:')
print('=' * 90)

for desc, amt in tests:
    result = cat.categorize(desc, amt)
    cat_str = f"{result['category']} / {result['subcategory']}"
    print(f"{desc:40} => {cat_str:35}")
    print(f"{'':40}    Reason: {result['reason']}")
    print()

print('=' * 90)
print('Test complete!')
