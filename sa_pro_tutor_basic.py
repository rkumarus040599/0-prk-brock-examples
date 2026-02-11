from typing import Any, Dict, Optional

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.runtime.context import RequestContext
from strands import Agent
from strands.models import BedrockModel

SYSTEM_PROMPT = """
You are an AWS Solutions Architect Professional (SAP-C02) exam tutor.
Your job is to:
- Explain AWS architecture concepts in simple language,
- Ask clarifying questions when the topic is vague,
- Create practice scenario questions (NOT real exam questions),
- Emphasize tradeoffs and AWS Well-Architected thinking,
- Never claim to know or reveal actual exam questions.

Be concise and structured. Focus on how to reason about architectures.
"""

# TODO: replace with your actual cheapest Bedrock model ID in us-east-1
BEDROCK_MODEL_ID = "us.amazon.nova-2-lite-v1:0"  # example only

bedrock_model = BedrockModel(
    model_id=BEDROCK_MODEL_ID,
    #region="us-east-1",
    temperature=0.3,
)

agent = Agent(system_prompt=SYSTEM_PROMPT, model=bedrock_model)

app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload: Dict[str, Any], context: Optional[RequestContext] = None) -> Dict[str, Any]:
    user_message = payload.get("prompt", "Help me prepare for the SA Pro exam.")
    result = agent(user_message)

    # Strands AgentResult → message → content[0].text
    try:
        message = getattr(result, "message", result)
        content = message.get("content", []) if isinstance(message, dict) else []
        if content and isinstance(content[0], dict) and "text" in content[0]:
            return {"result": content[0]["text"]}
    except Exception:
        pass

    # Fallbacks
    if isinstance(result, dict) and "content" in result:
        text = result["content"][0].get("text", "")
        return {"result": text}

    if hasattr(result, "message") and isinstance(result.message, dict) and "content" in result.message:
        text = result.message["content"][0].get("text", "")
        return {"result": text}

    # Last resort: string representation
    return {"result": str(result)}


if __name__ == "__main__":
    app.run()
