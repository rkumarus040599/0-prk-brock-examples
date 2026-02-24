agentcore configure \
  --name sa_pro_tutor_tools_2b_mcp_v4 \
  --entrypoint sa_pro_tutor_tools_2b_mcp_v4.py \
  --authorizer-config "{\"customJWTAuthorizer\":{\"discoveryUrl\":\"https://cognito-idp.us-east-1.amazonaws.com/us-east-1_zB6wpsDgs/.well-known/openid-configuration\",\"allowedClients\":[\"v1q13rdlbv5ustb3629r0aotm\"]}}" \
  --request-header-allowlist "Authorization"
