"""
Phase 2b-mcp – SA Pro tutor with calculator and Gateway cost tool.

This agent extends the basic Phase 1 SA Pro tutor and the Phase 2a calculator
version by adding an external cost estimation tool exposed via an
Amazon Bedrock AgentCore Gateway (MCP).

The request/response contract is the same as Phase 1:

- Input payload must contain: {"prompt": "<user question>"}
- Output is always: {"result": "<answer as plain text>"}

Behavior:

- For general SA Pro questions, the agent uses the underlying Bedrock model
  plus a calculator tool for precise numeric reasoning (throughput, capacity, cost).
- The agent also has access to a Gateway-exposed cost estimation tool via MCP,
  and should prefer calling this tool for cost estimation of the serverless
  SA Pro tutor pattern instead of guessing manually.
"""

from typing import Any, Dict, Optional

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.runtime.context import RequestContext
from strands import Agent
from strands.models import BedrockModel
from strands_tools import calculator  # from strands-agents-tools
from mcp.client.streamable_http import streamable_http_client
from strands.tools.mcp import MCPClient  # Strands MCP integration
import os
import uuid
import requests
import json  # for parsing tool JSON payloads
import logging
import httpx
from dotenv import load_dotenv

load_dotenv()  # local dev only; runtime will use Identity

logger = logging.getLogger(__name__)

BEDROCK_MODEL_ID = "us.amazon.nova-2-lite-v1:0"  # Same model as Phase 1

# ---------------------------------------------------------------------------
# AgentCore Identity configuration (Cognito M2M via OAuth2 credential provider)
# ---------------------------------------------------------------------------
# Your configured OAuth2 credential provider in AgentCore Identity:
# arn:aws:bedrock-agentcore:us-east-1:628342616348:token-vault/default/oauth2credentialprovider/cognito-oauth-client-ly80g
#
# In the next iteration, we will call AgentCore Identity to obtain an access
# token for this provider and scope "default-m2m-resource-server-kjrqvn/read",
# then pass that token into the Gateway calls.
#
# For now, we keep MCP_BEARER_TOKEN as a local/dev fallback so you can still
# run and test the code locally while we finish wiring Identity in runtime.

IDENTITY_OAUTH2_CREDENTIAL_PROVIDER_ARN = (
    "arn:aws:bedrock-agentcore:us-east-1:628342616348:"
    "token-vault/default/oauth2credentialprovider/cognito-oauth-client-ly80g"
)
IDENTITY_OAUTH2_SCOPE = "default-m2m-resource-server-kjrqvn/read"

# TODO: Replace this env-based fallback with an Identity access token in runtime.
MCP_BEARER_TOKEN = os.getenv("MCP_GATEWAY_BEARER_TOKEN", "")

logger.info(f"MCP token present (local fallback): {bool(MCP_BEARER_TOKEN)}")
print("MCP_BEARER_TOKEN length:", len(MCP_BEARER_TOKEN))

SYSTEM_PROMPT = """
You are an AWS Solutions Architect Professional (SA Pro) exam tutor with access
to a calculator tool and a serverless cost estimation tool exposed via an
AgentCore Gateway.

Your goals:
- Help the user reason about AWS architectures, trade-offs, and best practices.
- Use clear, structured explanations that mirror SA Pro exam reasoning.
- Highlight relevant AWS services, design patterns, and cost/performance/security considerations.

When the user asks a question:
- Restate the scenario briefly.
- Analyze requirements and constraints.
- Propose 1–2 architectures or options, explain pros/cons, and recommend one.
- When doing any numeric reasoning (capacity, throughput, cost), show intermediate steps in plain language.

When the user asks for cost estimation of the serverless SA Pro tutor architecture,
prefer calling your Gateway cost tool via MCP instead of guessing manually.
Keep answers focused, exam-oriented, and avoid implementation-level code unless the user explicitly asks for it.
""".strip()

app = BedrockAgentCoreApp()

# Configure MCP client to talk to your AgentCore Gateway (Streamable HTTP MCP server)
GATEWAY_ID = "br-gw-phase2b-8gdhp3fszf"
GATEWAY_MCP_URL = (
    "https://br-gw-phase2b-8gdhp3fszf.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
)

# ---------------------------------------------------------------------------
# Helper to obtain an access token for Gateway calls
# ---------------------------------------------------------------------------

def _get_gateway_access_token() -> str:
    """
    Get an access token to call the AgentCore Gateway.

    Today:
        - Uses MCP_BEARER_TOKEN from the environment (local/dev).
    Next iteration:
        - Will call AgentCore Identity using
          IDENTITY_OAUTH2_CREDENTIAL_PROVIDER_ARN and IDENTITY_OAUTH2_SCOPE
          to obtain a fresh access token for each call in the managed runtime.

    This function centralizes how we obtain the token so we only need to
    change logic in one place when wiring Identity.
    """
    if MCP_BEARER_TOKEN:
        return MCP_BEARER_TOKEN

    raise RuntimeError(
        "No access token available for Gateway. "
        "In local dev, set MCP_GATEWAY_BEARER_TOKEN; "
        "in runtime, this will be provided by AgentCore Identity."
    )

# ---------------------------------------------------------------------------
# Direct HTTP call helper (fallback / explicit tool call)
# ---------------------------------------------------------------------------

def call_gateway_estimate_cost_tool(
    daily_requests: int,
    region: str,
    lambda_duration_ms: Optional[int] = None,
    lambda_memory_mb: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Call the AgentCore Gateway MCP endpoint to invoke the cost estimation tool
    on the existing Lambda target using a simple HTTP client, then return a
    concise summary plus the raw JSON payload.
    """

    access_token = _get_gateway_access_token()

    # Build MCP request payload
    request_id = str(uuid.uuid4())
    arguments: Dict[str, Any] = {
        "dailyRequests": daily_requests,
        "region": region,
    }
    if lambda_duration_ms is not None:
        arguments["lambdaDurationMs"] = lambda_duration_ms
    if lambda_memory_mb is not None:
        arguments["lambdaMemoryMb"] = lambda_memory_mb

    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "tools/call",
        "params": {
            # Tool name as exposed by the Gateway (from tools/list)
            "name": "br-gw-lambda-target___estimateCost",
            "arguments": arguments,
        },
    }

    resp = requests.post(
        GATEWAY_MCP_URL.rstrip("/"),
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    # Basic JSON-RPC error handling
    if "error" in data:
        raise RuntimeError(f"Gateway MCP error: {data['error']}")

    # MCP CallToolResult shape: {"result": {"content": [...], "meta": ...}, ...}
    result = data.get("result", {})
    content = result.get("content", [])

    if isinstance(content, list) and content:
        first = content[0] or {}
        text = first.get("text")
        if text:
            # Tool returns its own JSON as a string; parse and summarize
            try:
                parsed = json.loads(text)
                est = parsed.get("monthlyCostEstimateUSD")
                breakdown = parsed.get("breakdown", {})
                lambda_total = breakdown.get("lambdaRequests", 0) + breakdown.get(
                    "lambdaDuration", 0
                )
                api_gw = breakdown.get("apiGateway", 0)

                summary = (
                    f"Estimated monthly cost: ${est} "
                    f"(Lambda: ${lambda_total}, API Gateway: ${api_gw})."
                )

                return {"summary": summary, "raw": parsed}
            except Exception:
                # If parsing fails, just surface the raw text
                return {"summary": text, "raw": text}

    # Fallback if shape is unexpected
    return {"summary": str(result), "raw": result}

# ---------------------------------------------------------------------------
# MCPClient transport for Strands (uses same token helper)
# ---------------------------------------------------------------------------

def create_streamable_http_transport():
    """
    Transport callable for MCPClient using Streamable HTTP.

    Uses a pre-configured httpx.AsyncClient with Authorization header.
    """

    if not GATEWAY_MCP_URL:
        raise RuntimeError("GATEWAY_MCP_URL is not set in the runtime environment")

    access_token = _get_gateway_access_token()

    print("Using MCP Gateway transport with httpx.AsyncClient auth header")

    # Pre-configured HTTP client with the bearer token
    http_client = httpx.AsyncClient(
        headers={
            "Authorization": f"Bearer {access_token}",
        }
    )

    # Returns: () -> async context manager
    return lambda: streamable_http_client(
        url=GATEWAY_MCP_URL,
        http_client=http_client,
    )

# ---------------------------------------------------------------------------
# Agent construction
# ---------------------------------------------------------------------------

# def _build_agent() -> Agent:
#     """
#     Create a Strands Agent wired to Amazon Bedrock, the calculator tool,
#     and the Gateway MCP tools via MCPClient.
#     """
#     model = BedrockModel(
#         model_id=BEDROCK_MODEL_ID,
#         # Relies on AWS_REGION / profile configuration.
#     )

#     # MCPClient uses the transport callable returned by create_streamable_http_transport
#     #mcp_client = MCPClient(create_streamable_http_transport())

#     agent = Agent(
#         system_prompt=SYSTEM_PROMPT,
#         model=model,
#         tools=[
#             calculator,  # local calculator tool
#             #mcp_client,  # Gateway MCP tools over MCP
#         ],
#     )

#     return agent


def _build_agent() -> Agent:
    """
    Create a Strands Agent wired to Amazon Bedrock and the calculator tool.
    """
    model = BedrockModel(
        model_id=BEDROCK_MODEL_ID,
    )

    # Increase loop limits via Agent kwargs supported in older Strands versions.
    agent = Agent(
        system_prompt=SYSTEM_PROMPT,
        model=model,
        tools=[
            calculator,
            # mcp_client,
        ],
    )

    return agent



# ---------------------------------------------------------------------------
# AgentCore Runtime entrypoint
# ---------------------------------------------------------------------------

@app.entrypoint
def invoke(payload: Dict[str, Any], context: Optional[RequestContext] = None) -> Dict[str, Any]:
    """
    AgentCore Runtime entrypoint.

    Expects:
        payload: {"prompt": "<SA Pro style question or scenario>"}

    Returns:
        {"result": "<answer as plain text>"}
    """
    prompt = payload.get("prompt", "") or ""

    if not prompt.strip():
        return {
            "result": (
                "Please provide a non-empty 'prompt' field with your SA Pro question, "
                "for example: 'Estimate data transfer cost for 3 TB/month between two Regions.'"
            )
        }

    # 1) Always let the Strands agent (with MCP tools) try first
    agent = _build_agent()
    result = agent(prompt)

    # Try to unwrap Strands result into plain text
    text_answer: Optional[str] = None
    if hasattr(result, "message") and isinstance(result.message, dict):
        content = result.message.get("content", [])
        if isinstance(content, list) and content:
            first = content[0] or {}
            text_answer = first.get("text", "")

    # If we got a non-empty answer, return it (MCP path or model-only answer)
    if text_answer and text_answer.strip():
        return {"result": text_answer}

    # 2) Optional fallback: if the user explicitly asks for the gateway cost tool
    #    and the agent did not give a good answer, call the manual helper.
    if "estimateCost" in prompt or "gateway cost tool" in prompt:
        fallback = call_gateway_estimate_cost_tool(
            daily_requests=10000,
            region="us-east-1",
            lambda_duration_ms=200,
            lambda_memory_mb=256,
        )
        return {"result": fallback["summary"]}

    # 3) Last resort: string representation of whatever we got
    return {"result": str(result)}

if __name__ == "__main__":
    # Optional local dev server (not used in AgentCore Runtime managed deployment)
    app.run()
