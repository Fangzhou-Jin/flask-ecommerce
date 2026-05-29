"""
Security utilities: password hashing and verification.

Uses Werkzeug built-ins to avoid storing plaintext passwords.
"""

from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password."""
    return generate_password_hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a hash."""
    return check_password_hash(password_hash, plain_password)
