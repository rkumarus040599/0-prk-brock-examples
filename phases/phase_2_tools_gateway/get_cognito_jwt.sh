#!/usr/bin/env bash
set -euo pipefail

# Expects: COGNITO_CLIENT_ID_NOSEC, COGNITO_CLIENT_SECRET_NOSEC, and COGNITO_TOKEN_URL
CLIENT_ID="${COGNITO_CLIENT_ID_NOSEC:?COGNITO_CLIENT_ID_NOSEC not set}"
CLIENT_SECRET="${COGNITO_CLIENT_SECRET_NOSEC:?COGNITO_CLIENT_SECRET_NOSEC not set}"
TOKEN_URL="${COGNITO_TOKEN_URL:?COGNITO_TOKEN_URL not set}"
# Example TOKEN_URL:
# https://my-domain-dq6614fl.auth.us-east-1.amazoncognito.com/oauth2/token

curl -sS \
  -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}" \
  "${TOKEN_URL}" \
  | jq -r '.access_token'
