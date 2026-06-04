"""Console entry point for the travel landmark agent."""

import argparse
import asyncio
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from time import perf_counter
from typing import cast

from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.agents.requirement.requirements.conditional import (
    ConditionalRequirement,
)
from beeai_framework.backend import ChatModel
from beeai_framework.errors import FrameworkError
from beeai_framework.middleware.trajectory import GlobalTrajectoryMiddleware
from beeai_framework.tools import Tool
from beeai_framework.tools.handoff import HandoffTool
from beeai_framework.tools.search.wikipedia import WikipediaTool
from beeai_framework.tools.think import ThinkTool
from beeai_framework.tools.weather import OpenMeteoTool

from travel_landmark_agent.policy_lookup import CompanyTravelPolicyLookup
from travel_landmark_agent.tools import get_local_dates
from travel_landmark_agent.travel_phrase import parse_travel_phrase

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_TRAVEL_POLICIES_PATH = _PROJECT_ROOT / "data" / "travel_policies.json"


def main(argv: Sequence[str] | None = None) -> int:
    """Run the travel landmark agent."""
    parser = _create_parser()
    args = parser.parse_args(argv)
    travel_phrase = args.travel_phrase.strip()

    if not travel_phrase:
        parser.print_usage(sys.stderr)
        return 2

    tag_aliases = _load_tag_aliases()

    try:
        parsed_travel_phrase = parse_travel_phrase(travel_phrase, tag_aliases)
    except ValueError:
        parser.print_usage(sys.stderr)
        return 2

    start_time = perf_counter()
    agent_response = asyncio.run(
        get_agent_response(travel_phrase, parsed_travel_phrase.city)
    )
    elapsed_time = perf_counter() - start_time

    print(agent_response)
    print(f"Elapsed time: {_format_elapsed_time(elapsed_time)}")
    return 0


async def get_agent_response(travel_phrase: str, city: str) -> str:
    """Return the agent response for a travel phrase."""
    # model_name = "ollama:granite3.2:2b"
    model_name = "ollama:granite3.3:8b"
    knowledge_agent = RequirementAgent(
        llm=ChatModel.from_name(model_name),
        tools=[ThinkTool(), WikipediaTool()],
        requirements=[
            ConditionalRequirement(ThinkTool, force_at_step=1),
            ConditionalRequirement(WikipediaTool, max_invocations=2),
        ],
        role="Knowledge Specialist",
        instructions=(
            "Use the Wikipedia tool to answer landmark questions. "
            "If Wikipedia returns no results, do not repeat the same query. "
            "Try one broader query using the city name only. "
            "If that also returns no results, "
            "provide a cautious answer from general knowledge."
        ),
    )

    weather_agent = RequirementAgent(
        llm=ChatModel.from_name(model_name),
        tools=[OpenMeteoTool()],
        role="Weather Specialist",
        instructions=(
            "You are a weather specialist. Return only the weather information "
            "needed by the main agent. If asked about non-weather topics, say "
            "they are outside your scope."
        ),
    )

    main_agent = RequirementAgent(
        name="MainAgent",
        llm=ChatModel.from_name(model_name),
        tools=[
            ThinkTool(),
            get_local_dates,
            CompanyTravelPolicyLookup(_TRAVEL_POLICIES_PATH),
            HandoffTool(
                knowledge_agent,
                name="KnowledgeLookup",
                description="Consult the Knowledge Agent for general questions.",
            ),
            HandoffTool(
                weather_agent,
                name="WeatherLookup",
                description="Consult the Weather Agent for weather forecasts only.",
            ),
        ],
        requirements=[
            ConditionalRequirement(ThinkTool, force_at_step=1),
            ConditionalRequirement(
                CompanyTravelPolicyLookup,
                min_invocations=1,
                max_invocations=1,
            ),
        ],
        middlewares=[GlobalTrajectoryMiddleware(included=[Tool])],
    )

    question = (
        f"If I {travel_phrase} next weekend, "
        "use the local dates tool to determine the dates. "
        "Then use the WeatherLookup tool for the weather forecast. "
        "Then use the KnowledgeLookup tool to find one famous historical landmark. "
        "Then use the CompanyTravelPolicyLookup tool to check company travel "
        "policies that apply to this trip. "
        "If the KnowledgeLookup tool does not return a result, "
        "answer the landmark question from memory. "
        "Only include company travel policies returned by the "
        "CompanyTravelPolicyLookup tool. Do not invent policy guidance. "
        "When using WeatherLookup or KnowledgeLookup, "
        f"pass the full destination exactly as: {city}. "
        f"When using CompanyTravelPolicyLookup, pass the travel phrase as: "
        f"{travel_phrase}. "
    )

    try:
        expectation = "Helpful and clear response."
        response = await main_agent.run(question, expected_output=expectation)
        return response.last_message.text
    except FrameworkError as err:
        return err.explain()


def _create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m travel_landmark_agent",
        description="Run the travel landmark agent for a travel phrase.",
    )
    parser.add_argument(
        "--travel-phrase",
        default="",
        help="Travel phrase, such as 'by train to Rome'.",
    )

    return parser


def _load_tag_aliases() -> dict[str, list[str]]:
    policies_data = _load_travel_policies()
    tag_aliases = policies_data.get("tag_aliases")

    if not isinstance(tag_aliases, dict):
        raise ValueError("Travel policies must define a tag_aliases object.")

    parsed_tag_aliases = cast(dict[object, object], tag_aliases)

    return _parse_tag_aliases(parsed_tag_aliases)


def _load_travel_policies() -> dict[str, object]:
    with _TRAVEL_POLICIES_PATH.open(encoding="utf-8") as policies_file:
        policies_data: object = json.load(policies_file)

    if not isinstance(policies_data, dict):
        raise ValueError("Travel policies must be a JSON object.")

    return cast(dict[str, object], policies_data)


def _parse_tag_aliases(tag_aliases: dict[object, object]) -> dict[str, list[str]]:
    parsed_aliases: dict[str, list[str]] = {}

    for tag, aliases in tag_aliases.items():
        if not isinstance(tag, str):
            raise ValueError("Travel policy tag names must be strings.")

        if not isinstance(aliases, list):
            raise ValueError("Travel policy tag aliases must be lists.")

        parsed_aliases[tag] = _parse_aliases(cast(list[object], aliases))

    return parsed_aliases


def _parse_aliases(aliases: list[object]) -> list[str]:
    parsed_aliases: list[str] = []

    for alias in aliases:
        if not isinstance(alias, str):
            raise ValueError("Travel policy tag aliases must be strings.")

        parsed_aliases.append(alias)

    return parsed_aliases


def _format_elapsed_time(elapsed_seconds: float) -> str:
    total_seconds = round(elapsed_seconds)
    minutes = total_seconds // 60
    seconds = total_seconds % 60

    return f"{minutes:02}:{seconds:02}"


if __name__ == "__main__":
    raise SystemExit(main())
