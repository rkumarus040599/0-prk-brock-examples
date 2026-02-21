"""
Phase 2b-mcp-v2 – Minimal runtime based on
`runtime_with_strands_and_bedrock_models` tutorial.

Features:
- BedrockAgentCoreApp runtime integration
- Strands Agent with a single Amazon Bedrock model
- Simple 'invoke' entrypoint that just answers the prompt
- No MCP, no Identity, no external tools
"""

from typing import Any, Dict, Optional

import logging

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.runtime.context import RequestContext
from strands import Agent
from strands.models import BedrockModel

# ----------------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("***** BUILD MARKER 2b-mcp-v2 STRANDS+BEDROCK FROM TUTORIAL *****")
logger.info("Phase 2b-mcp-v2 tutorial-style minimal runtime module imported")

# ----------------------------------------------------------------------------
# Model + system prompt (adapted from tutorial structure)
# ----------------------------------------------------------------------------

BEDROCK_MODEL_ID = "us.amazon.nova-2-lite-v1:0"

SYSTEM_PROMPT = """
You are an AWS Solutions Architect Professional (SA Pro) exam tutor.

You:
- Use clear, concise explanations.
- Rely only on your own reasoning (no external tools).
- Focus on what matters for the SA Pro exam.
""".strip()

# ----------------------------------------------------------------------------
# AgentCore app
# ----------------------------------------------------------------------------

app = BedrockAgentCoreApp()


def _build_agent() -> Agent:
    """
    Build a Strands Agent backed by a single Amazon Bedrock model,
    following the same pattern as the runtime_with_strands_and_bedrock_models tutorial.
    """
    logger.info("Building Strands Agent (tutorial-style, Bedrock model only) for 2b-mcp-v2")

    # In the tutorial, a BedrockModel is created and passed into Agent.
    model = BedrockModel(
        model_id=BEDROCK_MODEL_ID,
    )

    # Minimal agent: system prompt + model, no tools.
    agent = Agent(
        system_prompt=SYSTEM_PROMPT,
        model=model,
        tools=[],
    )

    logger.info("Strands Agent for 2b-mcp-v2 constructed successfully")
    return agent


@app.entrypoint
def invoke(
    payload: Dict[str, Any], context: Optional[RequestContext] = None
) -> Dict[str, Any]:
    """
    AgentCore Runtime entrypoint for 2b-mcp-v2 (tutorial-style minimal).

    Input:
        payload: {"prompt": "<SA Pro style question or scenario>"}

    Output:
        {"result": "<answer as plain text>"}
    """
    logger.info(">>> ENTERING invoke() 2b-mcp-v2 TUTORIAL-MINIMAL <<<")
    logger.info("invoke payload keys=%s", list(payload.keys()))
    prompt = (payload.get("prompt") or "").strip()
    logger.info("invoke prompt=%r", prompt)

    if not prompt:
        return {
            "result": (
                "Please provide a non-empty 'prompt', e.g.: "
                "'Explain the difference between ALB and NLB.'"
            )
        }

    agent = _build_agent()
    logger.info("Invoking Strands Agent for 2b-mcp-v2 (tutorial-style)")
    result = agent(prompt)
    logger.info("Strands Agent invocation completed for 2b-mcp-v2")

    text_answer: Optional[str] = None
    if hasattr(result, "message") and isinstance(result.message, dict):
        content = result.message.get("content", [])
        if isinstance(content, list) and content:
            first = content[0] or {}
            text_answer = first.get("text", "")

    if text_answer and text_answer.strip():
        return {"result": text_answer}

    return {"result": str(result)}
