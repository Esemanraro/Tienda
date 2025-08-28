def format_currency(value):
    """Formatea un número como moneda"""
    if value is None:
        return "A$ 0.00"
    try:
        return f"A$ {float(value):.2f}"
    except (ValueError, TypeError):
        return "A$ 0.00"

from datetime import datetime

def format_date(value, format='%B %d, %Y'):
    """Formatea una fecha en un formato legible."""
    if value is None:
        return ""
    try:
        # Ensure value is a datetime object, not just a date object for strftime
        if not isinstance(value, datetime):
            # If it's a date object, it doesn't have time info, which is fine for formatting date part
            # If it's something else, this will likely fail or be handled by the outer try-except
            pass # strftime will work on date objects too
        return value.strftime(format)
    except (AttributeError, ValueError):
        # Handle cases where value is not a date/datetime object or has an invalid format
        return str(value) # Return original value as string if formatting fails

def get_toy(toy_id):
    """Helper function to get toy by id"""
    from app.models import Toy
    try:
        return Toy.query.get(int(toy_id))
    except (ValueError, TypeError):
        return None

