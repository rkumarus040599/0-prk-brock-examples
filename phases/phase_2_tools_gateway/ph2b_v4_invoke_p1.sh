#!/usr/bin/env bash
set -euo pipefail

export AWS_PROFILE="prk-pers-6348"
export REGION="us-east-1"

# Use the same M2M client values you showed in env | grep COGNITO_
export COGNITO_CLIENT_ID_NOSEC="v1q13rdlbv5ustb3629r0aotm"
export COGNITO_CLIENT_SECRET_NOSEC="1rf2kjt569sq8dcu666de1tds0e5n9glvnpdbklsne5njlngocsv"
export COGNITO_TOKEN_URL="https://my-domain-dq6614fl.auth.us-east-1.amazoncognito.com/oauth2/token"

JWT="$(./get_cognito_jwt.sh)"

echo "JWT: ${JWT:0:50}..."
echo "JWT length: ${#JWT}"

curl -sS \
  -H "Authorization: Bearer ${JWT}" \
  -H "Content-Type: application/json" \
  -d '{
        "jsonrpc": "2.0",
        "id": "phase1-request",
        "method": "tools/list",
        "params": {
          "phase": 1
        }
      }' \
  "https://br-gw-phase2b-8gdhp3fszf.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"

