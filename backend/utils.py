import re

def normalize_email(email):
    if not email:
        return None
    email = email.lower()
    name, domain = email.split("@")

    if domain == "gmail.com":
        name = name.split("+")[0]
        name = name.replace(".", "")

    return f"{name}@{domain}"


def normalize_phone(phone):
    if not phone:
        return None
    return re.sub(r"\D", "", phone)
