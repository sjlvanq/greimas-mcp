# Greimasian Narrative Analysis (Cognitive MCP Server)

Hands-on MCP Lab: Implementation of an automated semiotic analysis system based on Greimas's Actantial Model. By leveraging the Model Context Protocol (MCP), the project provides Large Language Models (LLMs) with specialized tools to decode structural patterns and actantial roles within complex storytelling.

---

## System Concept:

Unlike traditional MCP servers that act as simple connectors to databases or external APIs, this server functions as a **specialized cognitive layer**.

When a client (like Claude Desktop) calls the tools in this server, a "Nested LLM" pattern occurs:

1. **Orchestrator Level:** The primary LLM (the client) identifies a need for structural narrative analysis.
2. **Specialist Level (This Server):** The MCP server receives the raw text and initiates its own internal intelligence cycle. It calls a dedicated instance of Claude configured with **Greimasian expert prompts** and strict JSON schemas.
3. **Refined Output:** The server doesn't just return raw data; it returns a **validated, structured semiotic interpretation**.

This architecture ensures that the structural analysis follows the formal rigor of the Actantial Model, providing the primary LLM with high-quality, pre-processed "narrative metadata" that would be difficult to extract through general conversation alone.

> **User** → **Claude (Client)** → **MCP Server** → *(Internal Call)* → **Claude (Specialist)** → **Valid JSON Result** → **Claude (Client)** → **User Answer**.

---

## Available Tools

### 1. `CheckNarrativeFeasibility`

Evaluates whether a provided text meets the structural requirements for a successful Greimasian Actantial Analysis.

* **Genre Requirement:** Verifies if the text is narrative fiction.
* **Desire Axis:** Identifies if a central subject-object relationship exists.
* **Narrative Dynamism:** Confirms a clear transformation process between initial and final states.

**Output Example:**

```json
{
  "result": {
    "genre_requirement": "Pass - Narrative Fiction",
    "desire_axis_identified": "Pass - The central desire axis is the 'last man on Earth' seeking to satisfy his isolation...",
    "dynamism_and_process_identified": "Pass - The text presents a clear transformation process...",
    "overall_result": "Pass"
  }
}
```

### 2. `ExtractActantScheme`

Extracts the full actantial framework from the text, mapping the six primary actants and their interconnections.

* **Actants Mapped:** Subject, Object of Value, Sender (Destinator), Receiver (Destination), Helper, and Opponent.
* **Narrative Programs:** Identifies main actions and their function within the plot.

**Output Example:**

```json
[
  {
    "scheme_id": "Principal_Scheme_1",
    "narrative_program_type": "Main Action",
    "actants": {
      "subject": "The last man on Earth",
      "object_of_value": "Discovering who is at the door",
      "destinator": "The unknown entity knocking on the door",
      "destination": "The last man on Earth",
      "helper": null,
      "opponent": null
    }
  }
]
```

---

## Setup and Installation

### Prerequisites

* Python 3.10 or higher.
* [uv](https://github.com/astral-sh/uv) (Recommended package manager).
* Anthropic API Key.

### Installation
1. Clone the repository and navigate to the project root.
2. Install the project in editable mode:
```bash
uv pip install -e .
```
3. Create a `.env` file based on the example:
```env
ANTHROPIC_API_KEY=your_api_key_here
CLAUDE_ANALIST_MODEL=claude-3-5-sonnet-20240620
LOG_LEVEL=INFO
LOG_DISABLE_FILE=0
```
---

## Usage & Integration

### Testing with MCP Inspector
To verify tools are correctly exposed without opening a full client:
```bash
npx @modelcontextprotocol/inspector uv run main.py
```
### Integration with Claude Desktop
```json
{
  "mcpServers": {
    "greimas-analyzer": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/greimas-mcp",
        "run",
        "main.py"
      ]
    }
  }
}

```
