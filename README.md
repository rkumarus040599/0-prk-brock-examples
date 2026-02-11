# SA Pro Tutor – Amazon Bedrock AgentCore + Strands

This project is my personal learning lab for building an AWS Solutions Architect Professional (SAP-C02) tutor agent using Amazon Bedrock AgentCore and the Strands Agents SDK.

The goal is to incrementally evolve a basic agent into a richer SA Pro study assistant (tools, memory, knowledge base, and evaluation), while keeping each step small and understandable.

### Repo layout convention
Repo root: baseline Phase 1 agent (sa_pro_tutor_basic.py) and this README only.
phases/: phase-specific main files, helpers, and notes for Phase 1+ and beyond (for example, phases/phase-1-basic/, phases/phase-2-tools-gateway/).

## Project structure
Current key files in this repo root:

- sa_pro_tutor_basic.py – basic SA Pro tutor agent:
  - Uses an Amazon Bedrock model (Nova 2 Lite inference profile).
  - Simple prompt → response flow with Strands Agent.
- .bedrock_agentcore.yaml – local AgentCore Runtime configuration, present locally (ignored in Git).
- Dockerfile – container definition for deploying to AgentCore Runtime.
- requirements.txt – Python dependencies.
- .venv/ – local virtual environment (ignored in Git).

Git ignores:

- .venv/
- .bedrock_agentcore.yaml
- Python cache files like __pycache__/, *.pyc (optional).

## How to run locally

1. Activate the virtual environment

   From the project root:

   - Linux/macOS:
     source .venv/bin/activate

   - Windows (PowerShell):
     .\.venv\Scripts\Activate.ps1

2. Launch the agent

   agentcore launch

3. Invoke the basic SA Pro tutor

   agentcore invoke '{"prompt": "Hello"}'

Example with a more detailed prompt:

   agentcore invoke '{"prompt": "Explain multi-Region active-active architectures at SA Pro level."}'

## Learning roadmap (flexible)

Planned directions (subject to change as I learn):

Phase 1 – Basic agent (current)
Canonical main file in repo root: sa_pro_tutor_basic.py
More notes and any variants: phases/phase-1-basic/

Phase 2 – Tools + Gateway (planned)
Main and helper files will live under: phases/phase-2-tools-gateway/

Phase 3 – Memory / knowledge base (planned)
Files will live under: phases/phase-3-memory/

Phase 4 – Evaluation & observability (planned)
Files will live under: phases/phase-4-eval-observability/

