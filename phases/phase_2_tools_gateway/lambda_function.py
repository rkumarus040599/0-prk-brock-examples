import math
from typing import Any, Dict

# Rough, simplified constants for experimentation ONLY.
# These are ballpark figures for Feb 2026 in us-east-1 and intentionally approximate.
LAMBDA_REQUEST_PRICE_PER_MILLION = 0.20      # USD per 1M requests after free tier (simplified) [web:266]
LAMBDA_PRICE_PER_GB_SECOND = 0.0000166667    # USD per GB-second (approx first tier) [web:266]
APIGW_HTTP_API_PRICE_PER_MILLION = 1.00      # USD per 1M requests [web:268][web:275]


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Experimental cost helper for the SA Pro tutor serverless pattern:
    API Gateway HTTP API + Lambda + (implicitly) AgentCore Gateway.

    Expected input (event):
    {
      "dailyRequests": 100,
      "region": "us-east-1",
      "lambdaMemoryMb": 512,
      "lambdaDurationMs": 200
    }

    Returns a JSON object with:
    - monthlyCostEstimateUSD (float)
    - breakdown (dict of component -> float)
    - assumptions (dict)
    - notes (list of strings)
    """

    # 1. Read inputs with safe defaults
    daily_requests = _safe_int(event.get("dailyRequests", 100), 100)
    region = str(event.get("region", "us-east-1"))
    lambda_memory_mb = _safe_int(event.get("lambdaMemoryMb", 512), 512)
    lambda_duration_ms = _safe_int(event.get("lambdaDurationMs", 200), 200)

    # 2. Derive monthly usage
    days_per_month = 30
    monthly_requests = daily_requests * days_per_month

    # Convert Lambda memory to GB and duration to seconds
    lambda_memory_gb = lambda_memory_mb / 1024.0
    lambda_duration_seconds = lambda_duration_ms / 1000.0

    # Total GB-seconds for Lambda
    total_gb_seconds = monthly_requests * lambda_memory_gb * lambda_duration_seconds

    # 3. Cost components (very simplified)

    # Lambda requests: price per 1M requests
    lambda_request_cost = (
        (monthly_requests / 1_000_000.0) * LAMBDA_REQUEST_PRICE_PER_MILLION
    )

    # Lambda duration: GB-seconds * price per GB-second
    lambda_duration_cost = total_gb_seconds * LAMBDA_PRICE_PER_GB_SECOND

    # API Gateway HTTP API requests (per 1M)
    api_gw_cost = (monthly_requests / 1_000_000.0) * APIGW_HTTP_API_PRICE_PER_MILLION

    # For now, we won’t model AgentCore or CloudWatch explicitly in dollars;
    # we just show the main serverless path.
    breakdown = {
        "lambdaRequests": round(lambda_request_cost, 4),
        "lambdaDuration": round(lambda_duration_cost, 4),
        "apiGateway": round(api_gw_cost, 4),
    }

    monthly_cost = sum(breakdown.values())

    # 4. Basic SA Pro–style notes
    notes = []

    if monthly_requests <= 100_000:
        notes.append(
            "At this traffic level, a serverless pattern (API Gateway + Lambda) "
            "is generally cost-efficient compared to running always-on EC2."
        )

    if monthly_requests > 1_000_000:
        notes.append(
            "As request volume grows beyond ~1M per month, evaluate alternatives "
            "such as ALB + ECS/Fargate or compute savings plans for steady workloads."
        )

    if lambda_duration_ms > 1000:
        notes.append(
            "The configured Lambda duration is relatively high; consider optimizing "
            "function performance or splitting work to reduce GB-seconds."
        )

    if not notes:
        notes.append(
            "This estimate is approximate and intended for SA Pro-style reasoning, "
            "not as a production billing calculator."
        )

    # 5. Return structured response for the Gateway tool
    return {
        "monthlyCostEstimateUSD": round(monthly_cost, 4),
        "breakdown": breakdown,
        "assumptions": {
            "dailyRequests": daily_requests,
            "daysPerMonth": days_per_month,
            "billableRequestsPerMonth": monthly_requests,
            "lambdaMemoryMb": lambda_memory_mb,
            "lambdaDurationMs": lambda_duration_ms,
            "lambdaMemoryGb": round(lambda_memory_gb, 4),
            "lambdaDurationSeconds": round(lambda_duration_seconds, 4),
            "region": region,
            "pricingNote": (
                "Pricing constants are simplified and approximate for experimentation."
            ),
        },
        "notes": notes,
    }
