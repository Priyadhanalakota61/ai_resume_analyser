"""Conservative extraction of explicit durations; never infer tenure from education."""
import re
from decimal import Decimal

NUMBER = r'\d{1,2}(?:\.\d{1,2})?'
DURATION = rf'(?P<low>{NUMBER})\s*(?:(?:[-–—]|to)\s*(?P<high>{NUMBER})\s*)?(?:\+\s*)?(?P<unit>years?|yrs?|months?)'
AFTER = re.compile(rf'(?<![\w.]){DURATION}\s+(?:of\s+)?(?:(?:relevant|professional|work|commercial|industry|hands-on|overall|total)\s+)*experience\b', re.I)
BEFORE = re.compile(rf'\bexperience\s*(?::|of|with|required)?\s*(?:at least|minimum(?: of)?)?\s*{DURATION}\b', re.I)
OPTIONAL = re.compile(r'\b(preferred|desirable|ideally|optional|nice to have|up to|maximum|not required|no experience)\b', re.I)


def explicit_experience(text, *, job=False):
    found = []
    # Keep preference/upper-bound qualifiers in their sentence or bullet.
    for clause in re.split(r'[\n;]|(?<=[.!?])\s+', text):
        if job and OPTIONAL.search(clause):
            continue
        for pattern in (AFTER, BEFORE):
            for match in pattern.finditer(clause):
                low = Decimal(match['low'])
                high = Decimal(match['high']) if match['high'] else low
                if high < low:
                    continue
                months = low * (12 if match['unit'].lower().startswith(('year', 'yr')) else 1)
                if months > 600 or months != int(months):
                    continue
                found.append((int(months), match.group(0)))
    return list(dict.fromkeys(found))


def resume_experience_hint(text):
    values = explicit_experience(text)
    amounts = {months for months, _ in values}
    if len(amounts) == 1:
        return {'months': values[0][0], 'evidence': values[0][1]}
    return {'months': None, 'evidence': ''}


def job_experience(text):
    values = explicit_experience(text, job=True)
    if not values:
        return None, ''
    # All explicit requirements must be met; take the largest stated minimum.
    return max(values, key=lambda value: value[0])
