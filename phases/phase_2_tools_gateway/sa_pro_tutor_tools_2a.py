"""
Phase 2a – SA Pro tutor with a calculator tool (Strands).

This agent extends the basic Phase 1 SA Pro tutor by adding a calculator tool
for precise numeric reasoning (cost estimates, throughput, capacity sizing).
The request/response contract is the same as Phase 1:

- Input payload must contain: {"prompt": "<user question>"}
- Output is always: {"result": "<answer as plain text>"}
"""

from typing import Any, Dict, Optional

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.runtime.context import RequestContext
from strands import Agent
from strands.models import BedrockModel
from strands_tools import calculator  # from strands-agents-tools


"""
Phase 2a – SA Pro tutor with a calculator tool (Strands).

This agent extends the basic Phase 1 SA Pro tutor by adding a calculator tool
for precise numeric reasoning (cost estimates, throughput, capacity sizing).
The request/response contract is the same as Phase 1:

- Input payload must contain: {"prompt": "<user question>"}
- Output is always: {"result": "<answer as plain text>"}
"""


BEDROCK_MODEL_ID = "us.amazon.nova-2-lite-v1:0"  # Same model as Phase 1


SYSTEM_PROMPT = """
You are an AWS Solutions Architect Professional (SAP-C02) exam tutor.

Your job is to:
- Explain AWS architecture concepts clearly at SA Pro level.
- Help design and critique solutions for realistic exam-style scenarios.
- Call tools when you need them, especially for numeric reasoning.

You MUST use the calculator tool for:
- Cost estimation questions (e.g., data transfer, EC2 sizing, storage).
- Throughput/capacity math (e.g., IOPS, requests per second, multi-Region traffic).
- Any question where precise numeric calculations are required.

When using the calculator:
- Show your reasoning in words, not raw expressions.
- Summarize the result in business and architecture terms (implications, trade-offs).

When you do NOT need tools:
- Answer directly, focusing on patterns, trade-offs, and AWS best practices.

Always respond in a way that would help someone prepare for the SAP-C02 exam.

“When you use the calculator, you MAY include (wherever possible) the final numeric result explicitly in your answer (e.g., ‘Total cost = $135 per month’) after explaining the steps.”
"""

app = BedrockAgentCoreApp()


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
        tools=[calculator],
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
