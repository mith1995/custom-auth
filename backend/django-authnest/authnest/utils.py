import re

def normalize_email(email):
    email = (email or "").strip().lower()
    return email or None

def normalize_phone(phone):
    phone = re.sub(r"[\s\-()]","", phone or "")
    return phone or None