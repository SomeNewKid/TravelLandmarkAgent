"""Tests for the travel landmark agent entry point."""

from unittest.mock import patch

from _pytest.capture import CaptureFixture

from travel_landmark_agent import __main__ as main_module
from travel_landmark_agent.travel_phrase import TravelPhrase


def test_main_displays_usage_when_travel_phrase_argument_is_missing(
    capsys: CaptureFixture[str],
) -> None:
    """The console entry point requires a travel phrase argument."""
    exit_code = main_module.main([])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "usage:" in captured.err
    assert "--travel-phrase" in captured.err


def test_main_displays_usage_when_travel_phrase_argument_is_empty(
    capsys: CaptureFixture[str],
) -> None:
    """The console entry point rejects an empty travel phrase argument."""
    exit_code = main_module.main(["--travel-phrase", ""])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "usage:" in captured.err
    assert "--travel-phrase" in captured.err


def test_main_displays_elapsed_time(capsys: CaptureFixture[str]) -> None:
    """The console entry point prints elapsed agent runtime."""

    async def _get_agent_response(travel_phrase: str, city: str) -> str:
        return f"Agent response for {city}"

    with patch.object(main_module, "get_agent_response", _get_agent_response):
        with patch.object(main_module, "perf_counter", side_effect=[10.0, 385.0]):
            exit_code = main_module.main(["--travel-phrase", "by train to Rome"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == "Agent response for Rome\nElapsed time: 06:15\n"
    assert captured.err == ""


def test_main_passes_policy_tag_aliases_to_travel_phrase_parser(
    capsys: CaptureFixture[str],
) -> None:
    """The console entry point parses phrases with policy tag aliases."""
    captured_tag_aliases: dict[str, list[str]] = {}

    def _parse_travel_phrase(
        travel_phrase: str,
        tag_aliases: dict[str, list[str]],
    ) -> TravelPhrase:
        captured_tag_aliases.update(tag_aliases)
        return TravelPhrase(city="Rome", travel_tags=["plane"])

    async def _get_agent_response(travel_phrase: str, city: str) -> str:
        return f"Agent response for {city}"

    with patch.object(main_module, "parse_travel_phrase", _parse_travel_phrase):
        with patch.object(main_module, "get_agent_response", _get_agent_response):
            exit_code = main_module.main(["--travel-phrase", "by flight to Rome"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured_tag_aliases["plane"] == ["plane", "flight", "fly", "air"]
    assert captured_tag_aliases["train"] == ["train", "rail"]
    assert captured_tag_aliases["car"] == ["car", "drive", "driving"]
    assert captured_tag_aliases["ferry"] == ["ferry", "boat", "ship"]
    assert captured.out.startswith("Agent response for Rome\n")
    assert captured.err == ""
