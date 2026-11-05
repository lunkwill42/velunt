import secrets
import string

ALPHABET = string.ascii_letters + string.digits


def generate_public_id(length=6):
    """Generate a random alphanumeric ID."""
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def generate_host_token():
    """Generate a secret token, too long to be guessed or typed by hand."""
    return secrets.token_urlsafe(16)
