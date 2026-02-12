"""
Phase 2b – SA Pro tutor with calculator and Gateway cost tool.

This agent extends the basic Phase 1 SA Pro tutor and the Phase 2a calculator
version by adding an external cost estimation tool exposed via an
Amazon Bedrock AgentCore Gateway (MCP).

The request/response contract is the same as Phase 1:

- Input payload must contain: {"prompt": "<user question>"}
- Output is always: {"result": "<answer as plain text>"}

Behavior:

- For general SA Pro questions, the agent uses the underlying Bedrock model
  plus a calculator tool for precise numeric reasoning (throughput, capacity, cost).
- When the prompt explicitly mentions the Gateway cost tool (for example,
  contains "estimateCost" or "gateway cost tool"), the runtime directly calls
  the Gateway-exposed Lambda tool to estimate monthly cost for the
  serverless SA Pro tutor pattern and returns a concise textual summary.
"""


from typing import Any, Dict, Optional

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.runtime.context import RequestContext
from strands import Agent
from strands.models import BedrockModel
from strands_tools import calculator  # from strands-agents-tools
# from mcp.client.streamable_http import streamable_http_client
# from strands.tools.mcp import MCPClient  # Strands MCP integration
import os
import uuid
import requests
import json  # for parsing tool JSON payloads

BEDROCK_MODEL_ID = "us.amazon.nova-2-lite-v1:0"  # Same model as Phase 1
MCP_BEARER_TOKEN = os.getenv("MCP_GATEWAY_BEARER_TOKEN", "")

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

Keep answers focused, exam-oriented, and avoid implementation-level code unless the user explicitly asks for it.
""".strip()

app = BedrockAgentCoreApp()

# Configure MCP client to talk to your AgentCore Gateway (Streamable HTTP MCP server)
GATEWAY_ID = "br-gw-phase2b-8gdhp3fszf"
GATEWAY_MCP_URL = (
    "https://br-gw-phase2b-8gdhp3fszf.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
)


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
    
    if not MCP_BEARER_TOKEN:
        raise RuntimeError("MCP_GATEWAY_BEARER_TOKEN is not set in the runtime environment")

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
            "Authorization": f"Bearer {MCP_BEARER_TOKEN}",
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
                lambda_total = breakdown.get("lambdaRequests", 0) + breakdown.get("lambdaDuration", 0)
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


# def create_streamable_http_transport():
#     return streamable_http_client(
#         GATEWAY_MCP_URL,
#         {"Authorization": f"Bearer {MCP_BEARER_TOKEN}"},
#     )

# mcp_client = MCPClient(create_streamable_http_transport)


def _build_agent() -> Agent:
    """
    Create a Strands Agent wired to Amazon Bedrock and the calculator tool.

    - Uses BEDROCK_MODEL_ID as the underlying Bedrock model.
    - Adds the calculator tool so the agent can perform precise math.
    """
    model = BedrockModel(
        model_id=BEDROCK_MODEL_ID,
        # Do NOT pass region here; relies on AWS_REGION / profile configuration.
    )

    agent = Agent(
        system_prompt=SYSTEM_PROMPT,
        model=model,
        # tools=[calculator, mcp_client],
        tools=[calculator, call_gateway_estimate_cost_tool],
    )

    return agent


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

    # Simple heuristic: if user explicitly mentions the gateway cost tool, call it directly
    if "estimateCost" in prompt or "gateway cost tool" in prompt:
        result = call_gateway_estimate_cost_tool(
            daily_requests=10000,
            region="us-east-1",
            lambda_duration_ms=200,
            lambda_memory_mb=256,
        )
        # Use the cleaned-up summary for the client-facing result
        return {"result": result["summary"]}

    agent = _build_agent()
    result = agent(prompt)

    # Unwrap common Strands result shapes into plain text
    if hasattr(result, "message") and isinstance(result.message, dict):
        content = result.message.get("content", [])
        if isinstance(content, list) and content:
            first = content[0] or {}
            text = first.get("text", "")
            if text:
                return {"result": text}

    # Fallback: best-effort string representation
    return {"result": str(result)}


if __name__ == "__main__":
    # Optional local dev server (not used in AgentCore Runtime managed deployment)
    app.run()
