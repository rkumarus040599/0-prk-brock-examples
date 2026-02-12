import subprocess
import sys
from pathlib import Path

AGENT_NAME = "sa_pro_tutor_tools_2b"

def main():
    here = Path(__file__).parent
    script = here / "get_cognito_token.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("get_cognito_token.py failed:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)

    lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
    if not lines:
        print("No token returned from get_cognito_token.py", file=sys.stderr)
        sys.exit(1)
    token = lines[-1]

    print(
        "agentcore launch "
        "--code-build "
        f"--agent {AGENT_NAME} "
        "--auto-update-on-conflict "
        f'--env MCP_GATEWAY_BEARER_TOKEN="{token}"'
    )

if __name__ == "__main__":
    main()
