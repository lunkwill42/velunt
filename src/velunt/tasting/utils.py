import secrets
import string

ALPHABET = string.ascii_letters + string.digits


def generate_public_id(length=6):
    """Generate a random alphanumeric ID."""
    return "".join(secrets.choice(ALPHABET) for _ in range(length))
