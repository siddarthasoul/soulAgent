# SOUL

SOUL is an experimental AI agent platform I'm building to explore how different AI agents, tools, models, and verification systems can work together.

The project is currently **under development** and is not a final release.

## Current Direction

The system is being designed around:

* Multiple AI agents
* LLM provider abstraction
* Physics, chemistry, and math tools
* Research capabilities
* Visualization
* Agent verification
* RAG
* Memory
* Tool-based execution

## Architecture

The general flow is:

```text
User
  ↓
Query Router
  ↓
Agent / Task
  ↓
Tools / LLM
  ↓
Verification
  ↓
Response
```

The architecture will continue to evolve as new capabilities are added.

## LLM Providers

Currently experimenting with:

* Ollama
* Gemini
* NVIDIA

Provider configuration is handled through environment variables.

## Setup

Clone the repository:

```bash
git clone <repository-url>
cd soul
```

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create the environment file:

```bash
cp .env.example .env
```

Then configure the required API keys and model settings in `.env`.

## Status

**Work in progress**

Features, architecture, APIs, and project structure may change while development continues.

## Goal

The long-term goal is to build a modular AI system where agents can reason about a task, use appropriate tools, retrieve information, execute actions, and verify their results.
