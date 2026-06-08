# Travel Landmark Agent

A small Python agent built with IBM's BeeAI framework. It accepts a lightweight travel phrase, extracts the destination, checks next-weekend weather, looks up a landmark, retrieves matching company travel policies, and prints a short travel briefing.

> [!WARNING]
> This is an experimental project and should not be considered production-ready.

This is an experimental learning project rather than a production travel planner. Some shortcuts have been taken so the project can stay focused on learning the BeeAI framework.

## What it does

The application accepts a phrase such as:

```powershell
.\.venv\Scripts\python.exe -m travel_landmark_agent --travel-phrase "go by car and train to Christchurch, New Zealand"
```

It then:

- extracts the destination from the text after the last standalone `to`
- detects travel modes such as `plane`, `train`, `car`, and `ferry`
- uses BeeAI agents and tools to gather weather and landmark information
- retrieves relevant company travel policies from local JSON data
- prints the final response and elapsed runtime

## How it works

The main entry point is [__main__.py](C:/Git/TravelLandmarkAgent/src/travel_landmark_agent/__main__.py).

The agent uses:

- BeeAI `RequirementAgent` for the main agent and specialist agents
- Ollama as the local model provider
- `granite3.3:8b` as the configured model
- BeeAI `OpenMeteoTool` for weather forecasts
- BeeAI `WikipediaTool` for landmark lookup
- a custom local date tool for next-weekend dates
- a custom `CompanyTravelPolicyLookup` tool for simple structured RAG

The travel policy data lives in [data/travel_policies.json](C:/Git/TravelLandmarkAgent/data/travel_policies.json). The policy lookup tool reads this file, matches detected travel tags, and returns only the relevant policy statements.

## Requirements

- Python 3.11
- PowerShell
- Ollama
- The Ollama model used by the code, currently:

```powershell
ollama pull granite3.3:8b
```

If your machine struggles with the 8B model, the code can be changed back to the smaller model:

```python
model_name = "ollama:granite3.2:2b"
```

## Setup

Create and update the virtual environment with:

```powershell
.\scripts\setup-dev.ps1
```

This installs the project in editable mode with development dependencies.

## Run

Run the agent from the repository root:

```powershell
.\.venv\Scripts\python.exe -m travel_landmark_agent --travel-phrase "go by train to Rome"
```

The travel phrase must include a standalone `to`, because the current parser uses the text after the last `to` as the destination. This is a deliberate shortcut so the project can focus on tool use and agent orchestration, not on parsing intent from natural language.

## Checks

Run formatting, linting, type checking, and tests with:

```powershell
.\scripts\check.ps1
```

The script runs:

- `ruff format .`
- `ruff check .`
- `pyright`
- `pytest`

## Attribution

Weather data is provided by [Open-Meteo](https://open-meteo.com/) under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

Knowledge content may be retrieved from [Wikipedia](https://www.wikipedia.org/) under [CC BY-SA](https://creativecommons.org/licenses/by-sa/4.0/).

## Project layout

```text
data/
  travel_policies.json
src/
  travel_landmark_agent/
    __main__.py
    policy_lookup.py
    tools.py
    travel_phrase.py
tests/
scripts/
```

## Notes

The phrase parser is intentionally simple. It does not perform real named entity recognition or model-based classification.

The policy lookup is also intentionally small. It demonstrates the retrieval shape of RAG using structured JSON data rather than embeddings or a vector database. This keeps the retrieval step visible while avoiding infrastructure that would distract from the BeeAI tool flow.

## Third-Party Notices

This project has a direct runtime dependency on the `beeai-framework` Python package (Apache-2.0). See the package's PyPI license metadata for full license and notice terms.

## License

GNU General Public License v3.0. See the `LICENSE` file for details.
