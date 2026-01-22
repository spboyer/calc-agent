# Calculator Agent Deployment Fix Summary

**Date:** January 22, 2026  
**Status:** ✅ RESOLVED - Deployment Successful

## Problem

After 7+ deployment attempts, the calculator agent consistently failed with a 10-minute timeout during the "Starting agent container" phase. The container never reached a running state, preventing health checks from succeeding.

## Root Cause

The implementation was using the wrong client type and environment variables for the Azure AI hosted agent platform.

| Issue | What Was Used | What Was Needed |
|-------|---------------|-----------------|
| Client Type | `AzureAIClient` | `AzureAIAgentClient` |
| Endpoint Env Var | `AZURE_AI_PROJECT_ENDPOINT` | `FOUNDRY_PROJECT_ENDPOINT` |
| Model Env Var | `AZURE_AI_MODEL_DEPLOYMENT_NAME` | `FOUNDRY_MODEL_DEPLOYMENT_NAME` |
| Agent Creation | `.as_agent()` | `.create_agent()` |
| Python Version | 3.12-slim | 3.11-slim |
| Dependencies | Unpinned, missing packages | Pinned versions + uvicorn/fastapi |

## Changes Made

### 1. `src/CalculatorAgent/main.py`

**Before:**
```python
from agent_framework.azure import AzureAIClient

async def run_server():
    async with DefaultAzureCredential() as credential:
        agent = AzureAIClient(credential=credential).as_agent(
            name="CalculatorAgentAF",
            instructions="...",
            tools=tools,
        )
        await from_agent_framework(agent).run_async()
```

**After:**
```python
from agent_framework.azure import AzureAIAgentClient
from dotenv import load_dotenv

load_dotenv(override=True)

ENDPOINT = os.getenv("FOUNDRY_PROJECT_ENDPOINT", "")
MODEL_DEPLOYMENT_NAME = os.getenv("FOUNDRY_MODEL_DEPLOYMENT_NAME", "")

async def run_server():
    credential = DefaultAzureCredential()
    try:
        client = AzureAIAgentClient(
            project_endpoint=ENDPOINT,
            model_deployment_name=MODEL_DEPLOYMENT_NAME,
            credential=credential,
        )
        agent = client.create_agent(
            name="CalculatorAgentAF",
            model=MODEL_DEPLOYMENT_NAME,
            instructions="...",
            tools=tools,
        )
        await from_agent_framework(agent).run_async()
    finally:
        await credential.close()
```

### 2. `src/CalculatorAgent/agent.yaml`

**Before:**
```yaml
environment_variables:
  - name: AZURE_AI_PROJECT_ENDPOINT
    value: ${AZURE_AI_PROJECT_ENDPOINT}
  - name: AZURE_AI_MODEL_DEPLOYMENT_NAME
    value: ${AZURE_AI_MODEL_DEPLOYMENT_NAME}
```

**After:**
```yaml
environment_variables:
  - name: FOUNDRY_PROJECT_ENDPOINT
    value: ${AZURE_AI_PROJECT_ENDPOINT}
  - name: FOUNDRY_MODEL_DEPLOYMENT_NAME
    value: ${AZURE_AI_MODEL_DEPLOYMENT_NAME}
```

### 3. `src/CalculatorAgent/requirements.txt`

**Before:**
```
agent-framework-azure-ai
azure-ai-agentserver-agentframework
azure-monitor-opentelemetry==1.8.1
pytest==8.4.2
```

**After:**
```
# Pinned versions to avoid breaking changes
agent-framework-azure-ai==1.0.0b260107
agent-framework-core==1.0.0b260107

# Agent server for HTTP mode
azure-ai-agentserver-agentframework

# Web server (required by agent server)
uvicorn
fastapi

# Azure identity
azure-identity

# Environment variable loading
python-dotenv

# Monitoring
azure-monitor-opentelemetry==1.8.1

# Development
pytest==8.4.2
```

### 4. `src/CalculatorAgent/Dockerfile`

**Before:**
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . user_agent/
WORKDIR /app/user_agent
RUN if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
EXPOSE 8088
CMD ["python", "main.py"]
```

**After:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY ./ user_agent/
WORKDIR /app/user_agent
RUN if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
EXPOSE 8088
ENV PORT=8088
CMD ["python", "main.py"]
```

## Key Learnings

1. **`AzureAIAgentClient` vs `AzureAIClient`**: For hosted agents deployed via `azd` with `host: azure.ai.agent`, use `AzureAIAgentClient` which expects `FOUNDRY_*` environment variables.

2. **Environment Variable Mapping**: The `agent.yaml` maps azd environment variables to container environment variables. The container code must read from `FOUNDRY_PROJECT_ENDPOINT` and `FOUNDRY_MODEL_DEPLOYMENT_NAME`.

3. **Pin Dependencies**: The Agent Framework is in preview with frequent breaking changes. Pin to specific versions (e.g., `1.0.0b260107`) for stability.

4. **Include HTTP Server Dependencies**: The agent server framework requires `uvicorn` and `fastapi` to serve HTTP requests for health checks.

5. **Python 3.11**: Use Python 3.11-slim for better compatibility with current agent framework packages.

## Verification

**Deployment Result:**
```
SUCCESS: Your application was deployed to Azure in 2 minutes 3 seconds.
```

**Agent Endpoint:**
```
https://ai-account-fufkrevrlkiog.services.ai.azure.com/api/projects/ai-project-calc/agents/CalculatorAgentAF/versions/13
```

## Reference

The working implementation pattern was derived from the weather-agent example at `/Users/shboyer/github/weather-agent/priority_workflow.py`.
