from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)


def normalize_email(value):
    """Normalize an email address by stripping whitespace and lowercasing."""
    if value is None:
        return None

    normalized = value.strip().lower()
    return normalized or None


def format_currency(amount):
    """Format a number as currency with A$ prefix"""
    if amount is None:
        return "A$ 0.00"
    try:
        return f"A$ {float(amount):.2f}"
    except (TypeError, ValueError) as e:
        logger.error(f"Error formatting currency: {e}")
        return "A$ 0.00"

def generate_order_summary(order):
    """Generate a text summary of an order"""
    try:
        summary = []
        summary.append("🧾 Order Summary")
        summary.append("=" * 30)
        summary.append(f"📋 Order ID: {order.id}")
        summary.append(f"📅 Date: {order.order_date.strftime('%Y-%m-%d %H:%M:%S')}")
        summary.append(f"💰 Total: {format_currency(order.total_price)}")
        summary.append("\n🎁 Items:")
        
        for item in order.items:
            summary.append(f"  • {item.toy.name} x{item.quantity}: {format_currency(item.price * item.quantity)}")
        
        summary.append("\n✨ Thank you for shopping at ALOHA!")
        return "\n".join(summary)
    except Exception as e:
        logger.error(f"Error generating order summary: {e}")
        return "Error generating order summary"

def save_order_summary(order, output_file):
    """Save order summary to a text file"""
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        summary = generate_order_summary(order)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        return True
    except Exception as e:
        logger.error(f"Error saving order summary: {e}")
        return False

def calculate_order_total(items):
    """Calculate total price for a list of items"""
    try:
        return sum(item.price * item.quantity for item in items)
    except Exception as e:
        logger.error(f"Error calculating order total: {e}")
        return 0.0
