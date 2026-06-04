"""Tests for company travel policy lookup."""

import asyncio
import json
from pathlib import Path

from beeai_framework.tools import StringToolOutput

from travel_landmark_agent.policy_lookup import CompanyTravelPolicyLookup


def test_policy_lookup_returns_matching_policy_statements(
    tmp_path: Path,
) -> None:
    """The policy lookup returns policies matching detected transport tags."""
    policy_file = _write_policy_file(tmp_path)
    tool = CompanyTravelPolicyLookup(policy_file)
    query = (
        "If I go by train and car to Sydney next weekend, "
        "check the company travel policies that apply to this trip."
    )

    output = asyncio.run(_run_policy_lookup(tool, query))
    text = output.get_text_content()

    assert "Detected transport-mode tags: train, car." in text
    assert "rail-preferred: Train travel is preferred" in text
    assert "car-approval: Car travel over 300 kilometres" in text
    assert "economy-travel: Travellers must choose reasonable economy-class" in text
    assert "flight-booking" not in text
    assert "ferry-reimbursement" not in text


def test_policy_lookup_matches_aliases_case_insensitively(
    tmp_path: Path,
) -> None:
    """The policy lookup uses tag aliases in the policy file."""
    policy_file = _write_policy_file(tmp_path)
    tool = CompanyTravelPolicyLookup(policy_file)
    query = "If I FLY to Rome, check the company travel policies."

    output = asyncio.run(_run_policy_lookup(tool, query))
    text = output.get_text_content()

    assert "Detected transport-mode tags: plane." in text
    assert "flight-booking: Flights must be booked" in text
    assert "economy-travel: Travellers must choose reasonable economy-class" in text


def test_policy_lookup_reports_no_specific_policies_when_no_tags_match(
    tmp_path: Path,
) -> None:
    """The policy lookup reports clearly when no travel tags are detected."""
    policy_file = _write_policy_file(tmp_path)
    tool = CompanyTravelPolicyLookup(policy_file)

    output = asyncio.run(_run_policy_lookup(tool, "If I walk to the cafe."))
    text = output.get_text_content()

    assert "No transport-mode tags were detected" in text
    assert "No specific company travel policies apply." in text


def _write_policy_file(tmp_path: Path) -> Path:
    policy_file = tmp_path / "travel_policies.json"
    policy_file.write_text(
        json.dumps(
            {
                "tag_aliases": {
                    "plane": ["plane", "flight", "fly", "air"],
                    "train": ["train", "rail"],
                    "car": ["car", "drive", "driving"],
                    "ferry": ["ferry", "boat", "ship"],
                },
                "policies": [
                    {
                        "id": "flight-booking",
                        "tags": ["plane"],
                        "statement": (
                            "Flights must be booked through the company travel portal."
                        ),
                    },
                    {
                        "id": "rail-preferred",
                        "tags": ["train"],
                        "statement": (
                            "Train travel is preferred for short journeys "
                            "where practical."
                        ),
                    },
                    {
                        "id": "car-approval",
                        "tags": ["car"],
                        "statement": (
                            "Car travel over 300 kilometres requires manager approval."
                        ),
                    },
                    {
                        "id": "ferry-reimbursement",
                        "tags": ["ferry"],
                        "statement": (
                            "Ferry travel may be reimbursed when it is the "
                            "most practical route."
                        ),
                    },
                    {
                        "id": "economy-travel",
                        "tags": ["plane", "train", "car", "ferry"],
                        "statement": (
                            "Travellers must choose reasonable economy-class "
                            "or equivalent options."
                        ),
                    },
                ],
            },
        ),
        encoding="utf-8",
    )

    return policy_file


async def _run_policy_lookup(
    tool: CompanyTravelPolicyLookup,
    query: str,
) -> StringToolOutput:
    return await tool.run({"query": query})
