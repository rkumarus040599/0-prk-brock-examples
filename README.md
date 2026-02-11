# SA Pro Tutor – Amazon Bedrock AgentCore + Strands

This project is my personal learning lab for building an AWS Solutions Architect Professional (SAP-C02) tutor agent using Amazon Bedrock AgentCore and the Strands Agents SDK.

The goal is to incrementally evolve a basic agent into a richer SA Pro study assistant (tools, memory, knowledge base, and evaluation), while keeping each step small and understandable.

## Project structure

Current files:

- sa_pro_tutor_basic.py – basic SA Pro tutor agent:
  - Uses a Bedrock model (Nova 2 Lite inference profile).
  - Simple prompt → response flow with Strands Agent.
- .bedrock_agentcore.yaml – local AgentCore Runtime configuration (ignored in Git).
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

1. Phase 1 – Basic agent (current)
2. Phase 2 – Add simple tools (e.g., AWS APIs, docs lookup)
3. Phase 3 – Explore memory / knowledge base
4. Phase 4 – Add basic evaluation & observability
