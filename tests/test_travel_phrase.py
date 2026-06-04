"""Tests for lightweight travel phrase parsing."""

import pytest

from travel_landmark_agent.travel_phrase import extract_travel_tags, parse_travel_phrase


@pytest.fixture
def tag_aliases() -> dict[str, list[str]]:
    """Return travel tag aliases for tests."""
    return {
        "plane": ["plane", "flight", "fly", "air"],
        "train": ["train", "rail"],
        "car": ["car", "drive", "driving"],
        "ferry": ["ferry", "boat", "ship"],
    }


def test_extract_travel_tags_returns_multiple_matching_tags(
    tag_aliases: dict[str, list[str]],
) -> None:
    """Multiple travel methods can be matched in one phrase."""
    travel_tags = extract_travel_tags(
        "both drive and take a train to Sydney",
        tag_aliases,
    )

    assert travel_tags == ["train", "car"]


def test_extract_travel_tags_matches_aliases_case_insensitively(
    tag_aliases: dict[str, list[str]],
) -> None:
    """Aliases are matched without regard to case."""
    travel_tags = extract_travel_tags("FLY to Rome", tag_aliases)

    assert travel_tags == ["plane"]


def test_extract_travel_tags_matches_ferry_alias(
    tag_aliases: dict[str, list[str]],
) -> None:
    """A ferry alias maps to the ferry tag."""
    travel_tags = extract_travel_tags("by boat to Rottnest Island", tag_aliases)

    assert travel_tags == ["ferry"]


def test_extract_travel_tags_returns_empty_list_when_no_tags_match(
    tag_aliases: dict[str, list[str]],
) -> None:
    """Phrases without travel method aliases return no tags."""
    travel_tags = extract_travel_tags("walk to the cafe", tag_aliases)

    assert travel_tags == []


def test_extract_travel_tags_preserves_tag_alias_order(
    tag_aliases: dict[str, list[str]],
) -> None:
    """Tags are returned in the order defined by the aliases mapping."""
    travel_tags = extract_travel_tags(
        "take a ferry, then drive, then fly to Athens",
        tag_aliases,
    )

    assert travel_tags == ["plane", "car", "ferry"]


def test_parse_travel_phrase_extracts_city_after_last_to(
    tag_aliases: dict[str, list[str]],
) -> None:
    """The destination is the text after the last standalone 'to'."""
    travel_phrase = parse_travel_phrase(
        "take a train to Rome then ferry to Palermo",
        tag_aliases,
    )

    assert travel_phrase.city == "Palermo"
    assert travel_phrase.travel_tags == ["train", "ferry"]


def test_parse_travel_phrase_extracts_multiple_travel_tags(
    tag_aliases: dict[str, list[str]],
) -> None:
    """The parser extracts all travel tags before the destination."""
    travel_phrase = parse_travel_phrase(
        "take a car and train to Sydney",
        tag_aliases,
    )

    assert travel_phrase.city == "Sydney"
    assert travel_phrase.travel_tags == ["train", "car"]


def test_parse_travel_phrase_preserves_country_or_region_in_city(
    tag_aliases: dict[str, list[str]],
) -> None:
    """Commas and country names remain part of the destination."""
    travel_phrase = parse_travel_phrase(
        "by train and car to Christchurch, New Zealand",
        tag_aliases,
    )

    assert travel_phrase.city == "Christchurch, New Zealand"
    assert travel_phrase.travel_tags == ["train", "car"]


def test_parse_travel_phrase_matches_to_as_standalone_word(
    tag_aliases: dict[str, list[str]],
) -> None:
    """The parser does not split on 'to' inside another word."""
    travel_phrase = parse_travel_phrase(
        "fly nonstop to Tokyo",
        tag_aliases,
    )

    assert travel_phrase.city == "Tokyo"
    assert travel_phrase.travel_tags == ["plane"]


def test_parse_travel_phrase_rejects_phrase_without_destination(
    tag_aliases: dict[str, list[str]],
) -> None:
    """A phrase without a usable destination is invalid."""
    with pytest.raises(ValueError, match="travel destination"):
        parse_travel_phrase("take a train", tag_aliases)


def test_parse_travel_phrase_rejects_empty_destination(
    tag_aliases: dict[str, list[str]],
) -> None:
    """A phrase ending with 'to' has no destination."""
    with pytest.raises(ValueError, match="travel destination"):
        parse_travel_phrase("take a train to ", tag_aliases)
