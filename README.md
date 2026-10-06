# Engineering Team Agent with CrewAI

An AI-powered software engineering team built with **CrewAI** that takes high-level requirements, designs the system, implements it, tests it, and builds a Gradio interface.

The project simulates a collaborative engineering workflow where specialized AI agents work sequentially on the same shared sandbox.

## Architecture

```text
                    High-Level Requirements
                              │
                              ▼
                   ┌─────────────────────┐
                   │  Engineering Lead   │
                   │ Design & Delegation │
                   └──────────┬──────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
      ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
      │   Backend    │ │   Frontend   │ │     Test     │
      │   Engineer   │ │   Engineer   │ │   Engineer   │
      └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
             │                │                │
             └────────────────┼────────────────┘
                              ▼
                     Shared Sandbox
                              │
                              ▼
                    Working Application
```

## AI Engineering Team

### Engineering Lead
Responsible for:

- Analyzing high-level requirements
- Designing the system architecture
- Defining modules, classes, and functions
- Assigning work to the engineering team
- Providing Gradio 6 API guidance

### Backend Engineer
Responsible for:

- Implementing the backend from the design
- Writing clean Python code
- Using only the Python standard library
- Running backend checks and tests
- Providing a concise implementation handoff

### Frontend Engineer
Responsible for:

- Building the Gradio interface
- Connecting the UI to the backend
- Following modern Gradio APIs
- Supporting light and dark modes
- Creating a non-blocking validation script

### Test Engineer
Responsible for:

- Writing backend unit tests
- Using Python's built-in `unittest`
- Finding and fixing backend defects
- Re-running tests until they pass

## Example Project

The included workflow builds a **trading simulation account management system**.

The system supports:

- Account creation
- Depositing funds
- Withdrawing funds
- Buying shares
- Selling shares
- Holdings tracking
- Portfolio valuation
- Profit/loss calculation
- Transaction history
- Insufficient-balance protection
- Insufficient-holdings protection

Supported test share prices include:

| Symbol | Price |
|---|---:|
| AAPL | Fixed test price |
| TSLA | Fixed test price |
| GOOGL | Fixed test price |

The AI team then creates a professional **Gradio UI** to demonstrate the backend.

## Tech Stack

- **Python**
- **CrewAI**
- **LiteLLM**
- **Groq**
- **OpenRouter**
- **Gradio 6**
- **Context7 MCP**
- **uv**
- **Docker** for isolated sandbox execution
- Python `unittest`

## Shared Sandbox

All engineering agents work inside the same sandbox directory.

```text
sandbox/
├── design.md
├── trading_backend.py
├── test_trading_backend.py
├── app.py
└── _validate.py
```

This allows agents to hand off work through actual files instead of passing large source-code outputs between LLM calls.

## Workflow

The Crew runs sequentially:

```text
Requirements
     │
     ▼
Design
     │
     ▼
Backend Implementation
     │
     ▼
Gradio Frontend
     │
     ▼
Backend Testing
     │
     ▼
Validated Application
```

The **Engineering Lead** produces the design first.

The **Backend Engineer** then implements the design in the shared sandbox.

The **Frontend Engineer** reads the backend files directly from the sandbox and creates `app.py`.

Finally, the **Test Engineer** validates the backend and fixes defects when necessary.

## Project Structure

```text
engineering_team/
├── src/
│   └── engineering_team/
│       ├── crew.py
│       ├── main.py
│       ├── config/
│       │   ├── agents.yaml
│       │   └── tasks.yaml
│       └── tools/
│           └── sandbox_tool.py
├── sandbox/
├── pyproject.toml
└── README.md
```

## Running the Crew

Install the project dependencies with `uv` and configure the required API keys in your environment.

Then run:

```bash
uv run run_crew
```

Or, depending on the project's configured scripts:

```bash
uv run python -m engineering_team.main
```

The Crew will create and validate the application inside the shared `sandbox/` directory.

## Environment

The project uses separate LLM providers for different roles:

```text
Engineering Lead  → Groq
Backend Engineer  → OpenRouter
Frontend Engineer → Groq
Test Engineer     → OpenRouter
```

This allows different models/providers to be assigned according to the requirements of each engineering role.

## Design Principles

### File-Based Agent Handoffs

Agents communicate through the shared sandbox rather than unnecessarily copying entire source files into subsequent LLM prompts.

### Minimal Dependencies

The generated application uses only:

- Python standard library
- Gradio for the UI

### Validation Before Success

Agents are expected to actually run their code and tests.

A successful task means the implementation has been **executed and validated**, not simply generated.

### Specialized Agents

Each agent has a clearly defined responsibility, reducing overlap between architecture, implementation, frontend development, and testing.

## Why This Project?

This project explores how **multi-agent AI systems can automate parts of a real software engineering workflow**.

Instead of asking one LLM to build an entire application, the work is divided into specialized roles:

> **Design → Implement → Build UI → Test → Fix**

The result is a practical example of using **CrewAI for agentic software engineering workflows**.