# test_sheets.py
from dotenv import load_dotenv
load_dotenv()

from tools.sheets import get_all_contacts_raw, parse_name_from_url

# Test 1: Can we connect?
contacts = get_all_contacts_raw()
print(f"Found {len(contacts)} contacts")

# Test 2: Show first 3 rows
for c in contacts[:3]:
    print(c)

# Test 3: Name parsing
print(parse_name_from_url("https://www.linkedin.com/in/rumani-b-06596479/"))
# Should print: Rumani B