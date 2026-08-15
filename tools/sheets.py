import gspread
from google.oauth2.service_account import Credentials
import os
import re

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


def get_sheet():
    """Connect to Google Sheet and return the first worksheet."""
    creds = Credentials.from_service_account_file(
        "credentials.json", scopes=SCOPES
    )
    client = gspread.authorize(creds)
    sheet_name = os.getenv("GOOGLE_SHEET_NAME", "Networking Tracker")
    sheet = client.open(sheet_name)
    return sheet.sheet1


def parse_name_from_url(url: str) -> str:
    """
    Extract a human-readable name from a LinkedIn URL slug.
    linkedin.com/in/sarah-chen-capital-one → Sarah Chen Capital One
    linkedin.com/in/rumani-b-06596479 → Rumani B
    linkedin.com/in/harnoor7 → harnoor7 (username, can't parse)
    """
    if not url or "linkedin.com" not in str(url):
        return url  # Return as-is if it's an email or non-LinkedIn

    # Extract the slug after /in/
    match = re.search(r"linkedin\.com/in/([^/?]+)", url)
    if not match:
        return url

    slug = match.group(1)

    # Remove trailing hex/numeric IDs (like -06596479 or -ab7294148)
    slug = re.sub(r"-[a-f0-9]{6,}$", "", slug)

    # Remove trailing numbers that are clearly not part of a name
    slug = re.sub(r"\d+$", "", slug)

    # If slug has no hyphens, it's likely a username (e.g., "preritg", "harnoor7")
    # Still title-case it but flag it
    if "-" not in slug:
        # Single word slugs — could be a username or a single name
        return slug.title() if slug else url

    # Replace hyphens with spaces and title case
    name = slug.replace("-", " ").strip().title()

    return name


def get_all_contacts_raw() -> list[dict]:
    """
    Read all rows from the sheet as raw dicts.
    Returns the data exactly as it is — messy status, blank fields, everything.
    """
    sheet = get_sheet()
    records = sheet.get_all_records()
    return records


def format_sheet_for_llm() -> str:
    """
    Read the entire sheet and format it as a text block the LLM can understand.
    Each contact becomes a readable text entry with parsed name.
    """
    records = get_all_contacts_raw()

    if not records:
        return "The networking sheet is empty."

    lines = []
    lines.append(f"Total contacts: {len(records)}")
    lines.append(f"Today's date: {_today()}")
    lines.append("=" * 60)

    for i, row in enumerate(records, 1):
        link = str(row.get("Link", "")).strip()
        name = parse_name_from_url(link)

        entry = f"\n--- Contact #{i} ---\n"
        entry += f"Name (from URL): {name}\n"

        for key, value in row.items():
            val = str(value).strip()
            if val and val.lower() != "nan":
                entry += f"{key}: {val}\n"

        lines.append(entry)

    return "\n".join(lines)


def get_unique_companies() -> list[str]:
    """
    Get a deduplicated list of all companies in the sheet.
    Useful for future job search feature.
    """
    records = get_all_contacts_raw()
    companies = set()
    for row in records:
        company = str(row.get("Company", "")).strip()
        if company and company.lower() != "nan":
            companies.add(company)
    return sorted(companies)


def update_cell(row_index: int, column_name: str, value: str):
    """
    Update a specific cell in the sheet.
    row_index is 1-based (row 1 = header, row 2 = first data row).
    """
    sheet = get_sheet()
    headers = sheet.row_values(1)
    if column_name not in headers:
        return f"Column '{column_name}' not found"
    col_num = headers.index(column_name) + 1
    sheet.update_cell(row_index, col_num, value)
    return f"Updated row {row_index}, {column_name} = {value}"


def _today() -> str:
    from datetime import datetime
    return datetime.now().strftime("%B %d, %Y")