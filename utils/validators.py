import re

EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

def is_valid_email(email: str) -> bool:
    return re.fullmatch(EMAIL_REGEX, email) is not None