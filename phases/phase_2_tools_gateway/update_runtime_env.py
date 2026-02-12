import json
import subprocess
import sys
from pathlib import Path

RUNTIME_ID = "sa_pro_tutor_tools_2b-0khSMvCjuv"
REGION = "us-east-1"
PROFILE = "prk-pers-6348"


def get_access_token():
    here = Path(__file__).parent
    script = here / "get_cognito_token.py"
    if not script.exists():
        print(f"get_cognito_token.py not found at {script}", file=sys.stderr)
        sys.exit(1)

    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("get_cognito_token.py failed:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)

    # Take the last non-empty line from stdout (should be the token)
    lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
    if not lines:
        print("No token returned from get_cognito_token.py", file=sys.stderr)
        sys.exit(1)
    token = lines[-1]
    return token


def update_runtime_env(token: str):
    cmd = [
        "aws",
        "bedrock-agentcore-control",
        "update-agent-runtime",
        "--agent-runtime-id",
        RUNTIME_ID,
        "--environment-variables",
        f"MCP_GATEWAY_BEARER_TOKEN={token}",
        "--region",
        REGION,
        "--profile",
        PROFILE,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("Failed to update agent runtime:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)

    try:
        resp = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        resp = {}
    print("Updated runtime environment variables.")
    if resp:
        print(json.dumps(resp.get("environmentVariables", {}), indent=2))


def main():
    token = get_access_token()
    update_runtime_env(token)


if __name__ == "__main__":
    main()
