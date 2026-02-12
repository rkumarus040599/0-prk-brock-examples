import os
import sys
import base64
import json
from pathlib import Path

import requests


def load_env():
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        print(f".env not found at {env_path}. Create it and set COGNITO_* values.", file=sys.stderr)
        sys.exit(1)

    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def main():
    load_env()

    domain = os.environ.get("COGNITO_DOMAIN")
    client_id = os.environ.get("COGNITO_CLIENT_ID")
    client_secret = os.environ.get("COGNITO_CLIENT_SECRET")
    scope = os.environ.get("COGNITO_SCOPE")

    if not all([domain, client_id, client_secret, scope]):
        print(
            "Missing one or more env vars: "
            "COGNITO_DOMAIN, COGNITO_CLIENT_ID, COGNITO_CLIENT_SECRET, COGNITO_SCOPE",
            file=sys.stderr,
        )
        sys.exit(1)

    token_url = domain.rstrip("/") + "/oauth2/token"

    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    data = {
        "grant_type": "client_credentials",
        "scope": scope,
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {auth_header}",
    }

    resp = requests.post(token_url, headers=headers, data=data)
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        print("Token request failed:", e, file=sys.stderr)
        print("Response:", resp.text, file=sys.stderr)
        sys.exit(1)

    body = resp.json()
    access_token = body.get("access_token")
    expires_in = body.get("expires_in")

    if not access_token:
        print("No access_token in response:", json.dumps(body, indent=2), file=sys.stderr)
        sys.exit(1)

    # Print ONLY the token to stdout
    print(access_token)

    # Optional: metadata to stderr
    print(json.dumps({"expires_in": expires_in}, indent=2), file=sys.stderr)


if __name__ == "__main__":
    main()
