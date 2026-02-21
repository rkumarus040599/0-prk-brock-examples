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

### Phase 2b – SA Pro tutor with calculator + Gateway cost tool

- Extends Phase 2a by adding an external cost estimation tool exposed via
  an Amazon Bedrock AgentCore Gateway.
- The core agent (Strands + calculator) still answers general SA Pro questions.
- When the prompt explicitly mentions `estimateCost` or `gateway cost tool`,
  the runtime calls a Gateway-backed Lambda MCP tool
  (`br-gw-lambda-target___estimateCost`) to estimate the monthly cost of the
  serverless SA Pro tutor pattern and returns a concise summary.

To deploy:

1. Ensure the Gateway and Lambda tool are configured and synchronized
   (tool name appears in `tools/list` as `br-gw-lambda-target___estimateCost`). [web:900][web:902]
2. Set environment variables in your shell for local testing:
   - `GATEWAY_MCP_URL`
   - `MCP_GATEWAY_BEARER_TOKEN`
3. From `phases/phase_2_tools_gateway/`, generate and run the launch command:

   ```bash
   python print_launch_cmd.py
   # then copy-paste the printed `agentcore launch ...` command


Phase 3 – Memory / knowledge base (planned)
Files will live under: phases/phase-3-memory/

Phase 4 – Evaluation & observability (planned)
Files will live under: phases/phase-4-eval-observability/

======
Phase 2a – Calculator tool only
SA Pro tutor backed by Amazon Bedrock (`us.amazon.nova-2-lite-v1:0`) with a local calculator tool. No Gateway, no external tools.

Phase 2b – Gateway + Lambda (no MCP in agent)  
Gateway is configured to expose a Lambda-based cost estimation tool, but the agent does not yet call it via MCP. Used to validate Gateway→Lambda wiring in isolation.

Phase 2b-mcp-v3 – Gateway + Lambda via MCP (env-based bearer token)
Agent uses both the calculator tool and an MCP client to call the Gateway, which invokes the Lambda cost tool and returns a structured cost breakdown.
Authentication to the Gateway uses an environment-provided bearer token (`MCP_GATEWAY_BEARER_TOKEN`) obtained via a separate Cognito client-credentials helper script. Token retrieval is out-of-band, not yet automated by AgentCore Identity.
> Status: End-to-end path (agent → MCP → Gateway → Lambda cost tool) is working with an env-based bearer token. Identity-based outbound auth is planned for a later phase.

=========