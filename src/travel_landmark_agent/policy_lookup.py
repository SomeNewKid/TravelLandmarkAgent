"""Company travel policy lookup tool."""

import json
from pathlib import Path
from typing import Any, cast

from beeai_framework.context import RunContext
from beeai_framework.emitter import Emitter
from beeai_framework.tools import StringToolOutput, Tool, ToolRunOptions
from pydantic import BaseModel, Field

from travel_landmark_agent.travel_phrase import extract_travel_tags


class _Policy(BaseModel):
    id: str
    tags: list[str]
    statement: str


class CompanyTravelPolicyLookupInput(BaseModel):
    """Input for the company travel policy lookup tool."""

    query: str = Field(
        description=(
            "The user's full travel-related question. The tool scans this text "
            "for transport modes and returns matching company travel policies."
        ),
    )


class CompanyTravelPolicyLookup(
    Tool[CompanyTravelPolicyLookupInput, ToolRunOptions, StringToolOutput]
):
    """Retrieve company travel policy statements relevant to a travel question."""

    def __init__(
        self,
        policy_file: str | Path,
        options: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(options)
        self.policy_file = Path(policy_file)

    @property
    def name(self) -> str:
        return "CompanyTravelPolicyLookup"

    @property
    def description(self) -> str:
        return (
            "Retrieves company travel policy statements relevant to the user's "
            "travel question."
        )

    @property
    def input_schema(self) -> type[CompanyTravelPolicyLookupInput]:
        return CompanyTravelPolicyLookupInput

    def _create_emitter(self) -> Emitter:
        return Emitter.root().child(
            namespace=["tool", "company", "travel_policy_lookup"],
            creator=self,
        )

    async def _run(
        self,
        input: CompanyTravelPolicyLookupInput,
        options: ToolRunOptions | None,
        context: RunContext,
    ) -> StringToolOutput:
        tag_aliases = self._load_tag_aliases()
        policies = self._load_policies()
        matched_tags = extract_travel_tags(input.query, tag_aliases)

        if not matched_tags:
            return StringToolOutput(_format_no_tags_result())

        matched_policies = _find_matching_policies(matched_tags, policies)
        result = _format_result(matched_tags, matched_policies)

        return StringToolOutput(result)

    def _load_tag_aliases(self) -> dict[str, list[str]]:
        policy_data = self._load_policy_data()
        tag_aliases = policy_data.get("tag_aliases")

        if not isinstance(tag_aliases, dict):
            return {}

        return _parse_tag_aliases(cast(dict[object, object], tag_aliases))

    def _load_policies(self) -> list[_Policy]:
        policy_data = self._load_policy_data()
        policies = policy_data.get("policies")

        if not isinstance(policies, list):
            return []

        return _parse_policies(cast(list[object], policies))

    def _load_policy_data(self) -> dict[str, object]:
        with self.policy_file.open(encoding="utf-8") as policy_file:
            policy_data: object = json.load(policy_file)

        if not isinstance(policy_data, dict):
            return {}

        return cast(dict[str, object], policy_data)


def _parse_tag_aliases(tag_aliases: dict[object, object]) -> dict[str, list[str]]:
    parsed_tag_aliases: dict[str, list[str]] = {}

    for tag, aliases in tag_aliases.items():
        if not isinstance(tag, str):
            continue

        if not isinstance(aliases, list):
            continue

        parsed_tag_aliases[tag] = _parse_string_list(cast(list[object], aliases))

    return parsed_tag_aliases


def _parse_policies(policies: list[object]) -> list[_Policy]:
    parsed_policies: list[_Policy] = []

    for policy in policies:
        if not isinstance(policy, dict):
            continue

        parsed_policy = _parse_policy(cast(dict[str, object], policy))
        if parsed_policy is not None:
            parsed_policies.append(parsed_policy)

    return parsed_policies


def _parse_policy(policy: dict[str, object]) -> _Policy | None:
    policy_id = policy.get("id")
    tags = policy.get("tags")
    statement = policy.get("statement")

    if not isinstance(policy_id, str):
        return None

    if not isinstance(tags, list):
        return None

    if not isinstance(statement, str):
        return None

    parsed_tags = _parse_string_list(cast(list[object], tags))

    return _Policy(id=policy_id, tags=parsed_tags, statement=statement)


def _parse_string_list(values: list[object]) -> list[str]:
    parsed_values: list[str] = []

    for value in values:
        if isinstance(value, str):
            parsed_values.append(value)

    return parsed_values


def _find_matching_policies(
    matched_tags: list[str],
    policies: list[_Policy],
) -> list[_Policy]:
    matched_tag_set = set(matched_tags)

    return [policy for policy in policies if matched_tag_set.intersection(policy.tags)]


def _format_no_tags_result() -> str:
    return "\n".join(
        [
            "No transport-mode tags were detected in the user question.",
            "No specific company travel policies apply.",
        ]
    )


def _format_result(
    matched_tags: list[str],
    matched_policies: list[_Policy],
) -> str:
    lines = [
        f"Detected transport-mode tags: {', '.join(matched_tags)}.",
    ]

    if not matched_policies:
        lines.append("No matching company travel policy statements were found.")
        return "\n".join(lines)

    lines.append("Relevant company travel policies:")

    for policy in matched_policies:
        lines.append(f"- {policy.id}: {policy.statement}")

    return "\n".join(lines)
