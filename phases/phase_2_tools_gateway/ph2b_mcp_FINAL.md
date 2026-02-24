prerequisites:
--------------
1. You must already have:
An AWS account with AgentCore and Cognito enabled in us-east-1.
IAM permissions to create AgentCore runtimes and gateways.
jq, curl, agentcore CLI, and AWS CLI installed.

2. Common pitfalls:
Wrong Cognito app client (user-password vs client-credentials).
Using ID token instead of access token.
Gateway configured with a different client ID/audience than the M2M client.
Forgetting to update COGNITO_TOKEN_URL to their own domain.


-------Phase 2b – MCP Gateway (v4) with Cognito M2M -----------
This phase shows how to:
Configure an AgentCore Runtime and Gateway.
Secure the Gateway with Cognito OAuth2 client credentials (M2M).
Talk to the Gateway as an MCP server using JSON‑RPC:

Phase 1: tools/list

Phase 2: tools/call for a Lambda cost tool

The goal is a repeatable pattern that anyone who forks this repo can run.

1. Components in this phase
AgentCore Runtime
Runs your agent code (e.g., agent.py) using the MCP protocol.

AgentCore Gateway
Front‑door HTTP endpoint that exposes your agent tools as an MCP server at /mcp and validates Bearer tokens (JWT).

Amazon Cognito (User Pool + Domain + App Client)
Issues access tokens via the client credentials flow (machine‑to‑machine) that the Gateway validates.

Local helper scripts

get_cognito_jwt.sh: get a Cognito access token via client credentials.

ph2b_v4_invoke_p1.sh: call tools/list on the Gateway.

ph2b_v4_invoke_p2.sh: call tools/call for the Lambda cost tool.

2. Identity / OAuth configuration (what you actually need)
This is the part that’s usually hand‑waved as “identity / OAuth options”. Here it is explicitly.

2.1 Cognito setup
You need one Cognito User Pool with:

User Pool Domain

Example:

text
https://my-domain-dq6614fl.auth.us-east-1.amazoncognito.com
App Client for M2M (client credentials)

Create an app client that:

Supports the client credentials grant.

Has a client ID and client secret.

Is associated with a resource server and scope, e.g.:

Resource server: default-m2m-resource-server-kjrqvn

Scope: default-m2m-resource-server-kjrqvn/read.

In your environment this looks like:

text
COGNITO_CLIENT_ID_NOSEC    = v1q13rdlbv5ustb3629r0aotm
COGNITO_CLIENT_SECRET_NOSEC= 1rf2kjt5...
COGNITO_TOKEN_URL          = https://my-domain-dq6614fl.auth.us-east-1.amazoncognito.com/oauth2/token
COGNITO_SCOPE              = default-m2m-resource-server-kjrqvn/read
2.2 AgentCore Gateway inbound auth
When you created/configured the Gateway, you told it how to validate incoming JWTs (this is what “identity / OAuth options” really means).

Conceptually, the Gateway config contains something like:

Issuer (discovery URL)

Points to Cognito’s OIDC discovery for your user pool, e.g.:

text
https://cognito-idp.us-east-1.amazonaws.com/<userPoolId>/.well-known/openid-configuration
Allowed audiences / clients

Includes the app client ID from above:

text
v1q13rdlbv5ustb3629r0aotm
Allowed scopes (optional but common)

Includes the scope your client gets in its token, e.g.:

text
default-m2m-resource-server-kjrqvn/read
Token type

Expects access tokens (not ID tokens) with token_use: "access" from Cognito.

This is how the Gateway decides whether an Authorization: Bearer <jwt> is valid.

3. AgentCore Runtime flow (configure → launch → invoke)
This is about getting your agent running as an AgentCore Runtime.

3.1 Configure the runtime
You can wrap this in v4-configure.sh, but conceptually you run something like:

bash
agentcore configure \
  --name sa-pro-tutor-v4 \
  --entrypoint agent.py \
  --protocol MCP \
  --region us-east-1 \
  --idle-timeout-seconds 1800 \
  --max-lifetime-seconds 7200 \
  # plus: identity/inbound auth flags pointing at your Cognito setup
This writes a config file (often .bedrock_agentcore.yaml) describing:

Runtime name.

Entrypoint script.

Protocol (MCP).

Inbound auth (how tokens should be validated) so agentcore launch and Gateway know what to expect.

3.2 Launch the runtime
Deploy or start the runtime:

bash
agentcore launch
# or an equivalent script that calls the AWS CLI to create/update the runtime
This provisions the agent runtime in AWS (if you’re not running only local).

3.3 Invoke the runtime (optional sanity check)
Before worrying about the Gateway, you can test the agent directly:

bash
agentcore invoke \
  --name sa-pro-tutor-v4 \
  --payload '{"prompt": "Hello from direct runtime"}'
This confirms the runtime is healthy and your agent.py is wired correctly.

4. Gateway MCP flow (M2M JWT → /mcp → tools)
This is the core of ph2b-mcp-v4.

4.1 Get a JWT from Cognito (client credentials)
Script: get_cognito_jwt.sh

bash
#!/usr/bin/env bash
set -euo pipefail

CLIENT_ID="${COGNITO_CLIENT_ID_NOSEC:?COGNITO_CLIENT_ID_NOSEC not set}"
CLIENT_SECRET="${COGNITO_CLIENT_SECRET_NOSEC:?COGNITO_CLIENT_SECRET_NOSEC not set}"
TOKEN_URL="${COGNITO_TOKEN_URL:?COGNITO_TOKEN_URL not set}"

curl -sS \
  -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}" \
  "${TOKEN_URL}" \
  | jq -r '.access_token'
Usage:

bash
export COGNITO_CLIENT_ID_NOSEC="v1q13rdlbv5ustb3629r0aotm"
export COGNITO_CLIENT_SECRET_NOSEC="1rf2kjt5..."
export COGNITO_TOKEN_URL="https://my-domain-dq6614fl.auth.us-east-1.amazoncognito.com/oauth2/token"

./get_cognito_jwt.sh | head -c 50; echo
./get_cognito_jwt.sh | wc -c  # ~800–1000 chars
This returns an access token whose iss, aud/client_id, and scope match what the Gateway expects.

4.2 Phase 1 – list tools (discover what the Gateway exposes)
Script: ph2b_v4_invoke_p1.sh

bash
#!/usr/bin/env bash
set -euo pipefail

export AWS_PROFILE="prk-pers-6348"
export REGION="us-east-1"

export COGNITO_CLIENT_ID_NOSEC="v1q13rdlbv5ustb3629r0aotm"
export COGNITO_CLIENT_SECRET_NOSEC="1rf2kjt5..."
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
        "method": "tools/list"
      }' \
  "https://br-gw-phase2b-8gdhp3fszf.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
This sends a valid JSON‑RPC 2.0 request to the Gateway’s /mcp endpoint.

The Gateway:

Validates the JWT via Cognito (issuer, audience, scope).

Returns a list of tools, e.g.:

br-gw-lambda-target___estimateCost with its input schema.

4.3 Phase 2 – call a tool (cost estimation)
Script: ph2b_v4_invoke_p2.sh

bash
#!/usr/bin/env bash
set -euo pipefail

export AWS_PROFILE="prk-pers-6348"
export REGION="us-east-1"

export COGNITO_CLIENT_ID_NOSEC="v1q13rdlbv5ustb3629r0aotm"
export COGNITO_CLIENT_SECRET_NOSEC="1rf2kjt5..."
export COGNITO_TOKEN_URL="https://my-domain-dq6614fl.auth.us-east-1.amazoncognito.com/oauth2/token"

JWT="$(./get_cognito_jwt.sh)"

echo "JWT: ${JWT:0:50}..."
echo "JWT length: ${#JWT}"

curl -sS \
  -H "Authorization: Bearer ${JWT}" \
  -H "Content-Type: application/json" \
  -d '{
        "jsonrpc": "2.0",
        "id": "estimate-cost-request",
        "method": "tools/call",
        "params": {
          "name": "br-gw-lambda-target___estimateCost",
          "arguments": {
            "dailyRequests": 1000,
            "lambdaDurationMs": 200,
            "lambdaMemoryMb": 512,
            "region": "us-east-1"
          }
        }
      }' \
  "https://br-gw-phase2b-8gdhp3fszf.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
This calls the cost estimation tool via MCP.

The response contains:

monthlyCostEstimateUSD

A breakdown of Lambda requests, Lambda duration, and API Gateway.

The assumptions used (inputs, derived values, region, pricing note).

5. Recommended sequence for repo users
Clone repo and set up Python/venv if needed.

Create/configure Cognito user pool + domain + M2M app client (client credentials) + scope.

Configure AgentCore Runtime with v4-configure.sh (or equivalent agentcore configure).

Launch Runtime with agentcore launch / deploy.

Optionally test Runtime with agentcore invoke.

Set env vars for M2M:

bash
export COGNITO_CLIENT_ID_NOSEC=...
export COGNITO_CLIENT_SECRET_NOSEC=...
export COGNITO_TOKEN_URL=...
Run Phase 1:

bash
./ph2b_v4_invoke_p1.sh
Confirm tools list.

Run Phase 2:

bash
./ph2b_v4_invoke_p2.sh
Confirm cost estimate result.

Reference:
Think of two layers, each with its own steps: Runtime and Gateway MCP.

For this phase, users mostly interact via the shell scripts, but the runtime still needs to be configured/launched at least once.

1) Runtime layer (one‑time or infrequent)
This is the part you used earlier (and are mostly not touching in v4):

Run your configure script (e.g. v4-configure.sh)

This wraps agentcore configure to define the runtime: name, entrypoint, protocol, and identity/auth config.

Run your launch/deploy script (or agentcore launch)

This actually creates/updates the AgentCore Runtime in AWS.

(Optional) Run your runtime invoke script or agentcore invoke

Quick sanity check that the runtime itself behaves as expected.

These steps can be done once per version (or whenever you change the agent/runtime config).

2) Gateway MCP layer (what users run repeatedly in ph2b‑mcp‑FINAL)
Once the runtime + gateway infra exists:

get_cognito_jwt.sh

Helper script, not usually called directly; it’s used by p1/p2 to fetch a Cognito M2M access token.

ph2b_v4_invoke_p1.sh

Uses get_cognito_jwt.sh.

Calls Gateway /mcp with JSON‑RPC tools/list to discover tools.

ph2b_v4_invoke_p2.sh

Uses get_cognito_jwt.sh.

Calls Gateway /mcp with JSON‑RPC tools/call to invoke br-gw-lambda-target___estimateCost with arguments.

So, for repo users:

Initial setup (once per environment):

Run configure.sh (or manually agentcore configure).

Run the runtime launch script / agentcore launch.

Optionally run your runtime‑invoke script.

Day‑to‑day / tutorial steps for this phase:

Run ph2b_v4_invoke_p1.sh to list tools.

Run ph2b_v4_invoke_p2.sh to call the Lambda cost tool.

They don’t need to call agentcore configure and agentcore invoke by hand; the scripts you ship are the way they should do it, as long as you clearly document:

“Run v4-configure.sh and deploy the runtime first.”

“Then use ph2b_v4_invoke_p1.sh and ph2b_v4_invoke_p2.sh to interact with the Gateway via MCP.”

Thread is getting long. Start a new one for better answers.