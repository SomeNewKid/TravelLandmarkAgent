# Travel Landmark Agent

This is a small artificial intelligence (AI) travel agent built for the "100 AI agents in 100 days" project. We used it to learn how a local tool-using agent behaves when she has to combine weather, landmark lookup, and a tiny retrieval step. It is intentionally modest, which is often where the useful lessons hide.

## What the agent does

The agent accepts a short travel phrase such as `go by car and train to Christchurch, New Zealand`. It extracts the destination, detects travel modes, then produces a short travel briefing.

The briefing includes next-weekend weather, one landmark, and matching company travel policies. It also prints elapsed runtime, because waiting for a local model feels more educational when the stopwatch admits what happened.

## How the agent works

The command-line entry point parses the travel phrase before the BeeAI agent runs. A small Python parser finds the last standalone `to`, treats the following text as the city, and matches transport keywords against aliases in `data/travel_policies.json`.

The main BeeAI `RequirementAgent` uses Ollama with `granite3.2:2b`. It has a local date tool, a company policy lookup tool, and two sub-agents exposed through BeeAI's `HandoffTool`: one for weather and one for general knowledge.

The policy lookup is the retrieval augmented generation (RAG) piece. It reads structured JSON, retrieves only the policy statements matching detected travel tags, and returns those statements as tool output for the final answer.

## What is interesting

The agent shows a useful split between deterministic code and model reasoning. Python handles phrase parsing, tag matching, and policy retrieval. The model handles orchestration and final wording.

That split made the agent more reliable without turning it into a grand architecture diagram. We resisted the urge to add embeddings, a vector database, and three planning layers before breakfast.

## What was challenging

The local 2B model needed clear boundaries. When the weather sub-agent was asked too broadly, it sometimes answered landmark and policy questions too. Tight specialist instructions helped.

The policy tool also had to be required exactly once. Otherwise the agent might plan to use it, then skip it after another tool returned a plausible answer. Plausible is not the same as grounded, which is the whole point of the policy lookup.

## Intentional shortcuts

The phrase parser is deliberately simple. It does not do real named entity recognition or classification. It splits on the last `to` and uses keyword aliases.

The RAG data is a JSON file, not a database or vector store. That was enough to practice the important shape: retrieve relevant facts at runtime, then make the agent use those facts instead of inventing policy guidance.

## What was learned

Tool-using agents need more than tools. They need clear tool descriptions, scoped specialist agents, and requirements when a step must happen.

We also learned that RAG does not have to start with embeddings. For structured policy data, a small deterministic lookup can teach the retrieval pattern more clearly than a heavier stack.

The next question is how far we can push this simple shape before it deserves a real workflow. That is usually the moment when the architecture diagram starts looking hungry.

---

## At a glance

Language: Python

Framework: BeeAI framework

LLM: Ollama `granite3.2:2b` for agent reasoning

Deployment: Local Python script

Patterns: Tool-using agent, Multi-agent, RAG

Storage: JSON file

Features: RAG, Function calling, Tool use, Structured parsing

Protocols: JSON Schema

Integrations: Ollama, OpenMeteo weather API, Wikipedia, Local JSON file

Security: Local execution, Restricted tool scope
