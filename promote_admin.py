#!/usr/bin/env python3
"""Promote a user to administrator.

Usage:
    python promote_admin.py <username>
"""

import sys

from app import app, db
from app.models import User


def promote(username: str) -> None:
    """Promote the specified user to admin if they exist."""
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if user:
            user.is_admin = True
            db.session.commit()
            print(f"User '{username}' promoted to admin.")
        else:
            print(f"Error: User '{username}' not found.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python promote_admin.py <username>")
        sys.exit(1)
    promote(sys.argv[1])
