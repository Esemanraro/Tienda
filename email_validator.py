"""Minimal stub of the email_validator package for testing purposes."""

from types import SimpleNamespace


class EmailNotValidError(ValueError):
    """Exception raised when an email address is not valid."""


def validate_email(email, *_, **__):
    if email is None:
        raise EmailNotValidError('Email address is required')

    normalized = str(email).strip()
    if '@' not in normalized:
        raise EmailNotValidError('Email address must contain @')

    return SimpleNamespace(email=normalized)
