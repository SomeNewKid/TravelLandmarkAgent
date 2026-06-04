"""Helpers for parsing lightweight travel phrases."""

import re
from dataclasses import dataclass

_DESTINATION_SEPARATOR_PATTERN = re.compile(r"\bto\b", flags=re.IGNORECASE)


@dataclass(frozen=True)
class TravelPhrase:
    """Structured details extracted from a lightweight travel phrase."""

    city: str
    travel_tags: list[str]


def extract_travel_tags(
    travel_phrase: str,
    tag_aliases: dict[str, list[str]],
) -> list[str]:
    """Extract travel tags from a lightweight travel phrase."""
    phrase = travel_phrase.lower()
    matched_tags: list[str] = []

    for tag, aliases in tag_aliases.items():
        if any(alias in phrase for alias in aliases):
            matched_tags.append(tag)

    return matched_tags


def parse_travel_phrase(
    travel_phrase: str,
    tag_aliases: dict[str, list[str]],
) -> TravelPhrase:
    """Parse a lightweight travel phrase into destination and travel tags."""
    separator_matches = list(_DESTINATION_SEPARATOR_PATTERN.finditer(travel_phrase))
    if not separator_matches:
        raise ValueError("Expected travel destination after the word 'to'.")

    separator_match = separator_matches[-1]
    travel_method_phrase = travel_phrase[: separator_match.start()]
    city = travel_phrase[separator_match.end() :].strip()

    if not city:
        raise ValueError("Expected travel destination after the word 'to'.")

    travel_tags = extract_travel_tags(travel_method_phrase, tag_aliases)

    return TravelPhrase(city=city, travel_tags=travel_tags)
