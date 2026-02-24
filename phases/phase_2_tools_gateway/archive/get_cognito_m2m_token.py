"""
Helper script to obtain a Cognito OAuth2 access token (client credentials)
and print it so you can set MCP_GATEWAY_BEARER_TOKEN for AgentCore Gateway.

Usage (after setting the env vars below):

    python get_cognito_m2m_token.py

It will print:
    ACCESS_TOKEN=<token>

You can then use:
    agentcore launch --env "MCP_GATEWAY_BEARER_TOKEN=<token>"
"""

import os
import sys
import base64
import requests
from urllib.parse import urlencode


def get_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        print(f"Missing required environment variable: {name}", file=sys.stderr)
        sys.exit(1)
    return value


def get_cognito_client_credentials_token() -> str:
    """
    Call the Cognito /oauth2/token endpoint with client_credentials grant
    and return the access_token field.[web:366]
    """

    # Required env vars:
    #   COGNITO_DOMAIN: e.g., https://my-domain.auth.us-east-1.amazoncognito.com
    #   COGNITO_CLIENT_ID
    #   COGNITO_CLIENT_SECRET
    #   COGNITO_SCOPE (optional, defaults to "default-m2m-resource-server-kjrqvn/read")
    cognito_domain = get_env("COGNITO_DOMAIN").rstrip("/")
    client_id = get_env("COGNITO_CLIENT_ID")
    client_secret = get_env("COGNITO_CLIENT_SECRET")
    scope = os.getenv("COGNITO_SCOPE", "default-m2m-resource-server-kjrqvn/read")

    token_url = f"{cognito_domain}/oauth2/token"

    # Use client_secret_basic auth (Authorization: Basic base64(client_id:client_secret))[web:366]
    basic_auth = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("utf-8")
    headers = {
        "Authorization": f"Basic {basic_auth}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    body = {
        "grant_type": "client_credentials",
        "scope": scope,
    }

    resp = requests.post(token_url, headers=headers, data=urlencode(body), timeout=30)
    resp.raise_for_status()
    data = resp.json()

    access_token = data.get("access_token")
    if not access_token:
        print(f"Response JSON did not contain access_token: {data}", file=sys.stderr)
        sys.exit(1)

    return access_token


if __name__ == "__main__":
    token = get_cognito_client_credentials_token()
    # Print in a shell-friendly format you can copy-paste
    #print(f"ACCESS_TOKEN={token}")
    print(token)
