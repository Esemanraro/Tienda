"""Utilities for collecting and normalizing center information."""
from __future__ import annotations

from typing import Dict, Iterable, List, Sequence, Tuple

from sqlalchemy import func

from ..extensions import db
from ..models import Center, Order, ToyCenterAvailability, User


def normalize_center_slug(value: str | None) -> str:
    """Normalize user-provided center identifiers into a slug."""
    if not value:
        return ""
    return value.strip().lower()


def _friendly_name_from_slug(slug: str) -> str:
    """Generate a human readable name for a slug when no official name exists."""
    if not slug:
        return ""
    cleaned = slug.replace("_", " ").replace("-", " ")
    return " ".join(part.capitalize() for part in cleaned.split()) or slug


def _record_slug(slug: str | None, slug_to_name: Dict[str, str]) -> None:
    normalized = normalize_center_slug(slug)
    if not normalized:
        return
    slug_to_name.setdefault(normalized, _friendly_name_from_slug(normalized))


def collect_center_choices() -> Tuple[List[Tuple[str, str]], Dict[str, str]]:
    """Aggregate center slugs from multiple sources and return choices and a lookup map."""
    slug_to_name: Dict[str, str] = {}

    try:
        center_rows: Sequence[Tuple[str, str]] = db.session.query(Center.slug, Center.name).all()
        for slug, name in center_rows:
            normalized = normalize_center_slug(slug)
            if not normalized:
                continue
            display_name = name or _friendly_name_from_slug(normalized)
            slug_to_name[normalized] = display_name

        # Gather legacy or user-entered slugs that might not have official Center rows yet
        legacy_queries: Sequence[Iterable[str]] = (
            (value for (value,) in db.session.query(User.center).filter(User.center.isnot(None), func.length(User.center) > 0).distinct()),
            (value for (value,) in db.session.query(ToyCenterAvailability.center).filter(ToyCenterAvailability.center.isnot(None), func.length(ToyCenterAvailability.center) > 0).distinct()),
            (value for (value,) in db.session.query(Order.discount_center).filter(Order.discount_center.isnot(None), func.length(Order.discount_center) > 0).distinct()),
        )
        for query in legacy_queries:
            for raw_slug in query:
                _record_slug(raw_slug, slug_to_name)

    except Exception:
        # Fall back to whatever we managed to gather so far.
        pass

    choices = sorted(((slug, name) for slug, name in slug_to_name.items()), key=lambda item: item[1].lower())
    return choices, slug_to_name
