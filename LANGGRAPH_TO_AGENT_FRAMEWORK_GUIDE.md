# LangGraph to Microsoft Agent Framework Migration Guide

A practical guide for migrating Python agents from LangGraph to Microsoft Agent Framework for deployment as hosted agents on Azure.

## Overview

| Aspect | LangGraph | Microsoft Agent Framework |
|--------|-----------|---------------------------|
| Pattern | StateGraph with nodes | AzureAIAgentClient with tools |
| State Management | Explicit state dict | Managed by framework |
| Tool Definition | `@tool` decorator | Annotated functions |
| Execution | `graph.invoke()` / `graph.stream()` | `agent.run_async()` via agent server |
| Deployment | Custom (FastAPI, etc.) | `azure.ai.agentserver.agentframework` |

## Step-by-Step Migration

### Step 1: Convert Tool Definitions

**LangGraph:**
```python
from langchain_core.tools import tool

@tool
def multiply(a: int, b: int) -> int:
    """Multiply a and b."""
    return a * b
```

**Agent Framework:**
```python
from typing import Annotated

def multiply(
    a: Annotated[int, "The first integer to multiply"],
    b: Annotated[int, "The second integer to multiply"]
) -> int:
    """Multiply a and b.

    Args:
        a: first int
        b: second int
    """
    return a * b
```

**Key differences:**
- Remove `@tool` decorator
- Use `Annotated[type, "description"]` for parameter descriptions
- Keep docstrings for function-level descriptions

### Step 2: Replace StateGraph with AzureAIAgentClient

**LangGraph:**
```python
from langgraph.graph import StateGraph, MessagesState
from langchain_openai import AzureChatOpenAI

llm = AzureChatOpenAI(model="gpt-4o-mini")
llm_with_tools = llm.bind_tools([multiply, add, divide])

graph_builder = StateGraph(MessagesState)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", ToolNode(tools=[multiply, add, divide]))
graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")
graph = graph_builder.compile()
```

**Agent Framework:**
```python
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import DefaultAzureCredential

ENDPOINT = os.getenv("FOUNDRY_PROJECT_ENDPOINT", "")
MODEL_DEPLOYMENT_NAME = os.getenv("FOUNDRY_MODEL_DEPLOYMENT_NAME", "")

credential = DefaultAzureCredential()
client = AzureAIAgentClient(
    project_endpoint=ENDPOINT,
    model_deployment_name=MODEL_DEPLOYMENT_NAME,
    credential=credential,
)

agent = client.create_agent(
    name="CalculatorAgent",
    model=MODEL_DEPLOYMENT_NAME,
    instructions="You are a helpful assistant...",
    tools=[multiply, add, divide],
)
```

### Step 3: Convert Execution Pattern

**LangGraph (local execution):**
```python
result = graph.invoke({"messages": [("user", "What is 5 * 3?")]})
print(result["messages"][-1].content)
```

**Agent Framework (hosted agent server):**
```python
from azure.ai.agentserver.agentframework import from_agent_framework

async def run_server():
    credential = DefaultAzureCredential()
    try:
        client = AzureAIAgentClient(...)
        agent = client.create_agent(...)
        
        # Run as HTTP server for hosted deployment
        await from_agent_framework(agent).run_async()
    finally:
        await credential.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_server())
```

### Step 4: Update Dependencies

**LangGraph requirements.txt:**
```
langgraph
langchain-openai
langchain-core
```

**Agent Framework requirements.txt:**
```
# Pin versions to avoid breaking changes
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
```

### Step 5: Create Deployment Configuration

**agent.yaml:**
```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/microsoft/AgentSchema/refs/heads/main/schemas/v1.0/ContainerAgent.yaml

kind: hosted
name: YourAgentName
description: Your agent description
metadata:
    authors:
        - your-name
    tags:
        - your-tag
protocols:
    - protocol: responses
      version: v1
environment_variables:
  - name: FOUNDRY_PROJECT_ENDPOINT
    value: ${AZURE_AI_PROJECT_ENDPOINT}
  - name: FOUNDRY_MODEL_DEPLOYMENT_NAME
    value: ${AZURE_AI_MODEL_DEPLOYMENT_NAME}
  - name: APPLICATIONINSIGHTS_CONNECTION_STRING
    value: ${APPLICATIONINSIGHTS_CONNECTION_STRING}
```

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY ./ user_agent/
WORKDIR /app/user_agent

RUN if [ -f requirements.txt ]; then \
        pip install -r requirements.txt; \
    else \
        echo "No requirements.txt found"; \
    fi

EXPOSE 8088
ENV PORT=8088

CMD ["python", "main.py"]
```

**azure.yaml:**
```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/Azure/azure-dev/main/schemas/v1.0/azure.yaml.json

requiredVersions:
    extensions:
        azure.ai.agents: '>=0.1.0-preview'
name: your-project-name
services:
    YourAgentService:
        project: src/YourAgent
        host: azure.ai.agent
        language: docker
        docker:
            remoteBuild: true
        config:
            container:
                resources:
                    cpu: "1"
                    memory: 2Gi
                scale:
                    maxReplicas: 3
                    minReplicas: 1
            deployments:
                - model:
                    format: OpenAI
                    name: gpt-4o-mini
                    version: "2024-07-18"
                  name: gpt-4o-mini
                  sku:
                    capacity: 10
                    name: GlobalStandard
infra:
    provider: bicep
    path: ./infra
```

## Complete Migration Example

### Before (LangGraph)

```python
# calculator_agent.py
from typing import Annotated
from langchain_openai import AzureChatOpenAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition

@tool
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

@tool
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

@tool
def divide(a: int, b: int) -> float:
    """Divide two numbers."""
    return a / b

tools = [multiply, add, divide]
llm = AzureChatOpenAI(model="gpt-4o-mini")
llm_with_tools = llm.bind_tools(tools)

def chatbot(state: MessagesState):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

graph_builder = StateGraph(MessagesState)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", ToolNode(tools=tools))
graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")
graph = graph_builder.compile()

if __name__ == "__main__":
    result = graph.invoke({"messages": [("user", "What is 25 * 4?")]})
    print(result["messages"][-1].content)
```

### After (Agent Framework)

```python
# main.py
import asyncio
import os
from typing import Annotated
from azure.identity.aio import DefaultAzureCredential
from agent_framework.azure import AzureAIAgentClient
from azure.ai.agentserver.agentframework import from_agent_framework
from dotenv import load_dotenv

load_dotenv(override=True)

ENDPOINT = os.getenv("FOUNDRY_PROJECT_ENDPOINT", "")
MODEL_DEPLOYMENT_NAME = os.getenv("FOUNDRY_MODEL_DEPLOYMENT_NAME", "")


def multiply(
    a: Annotated[int, "The first integer to multiply"],
    b: Annotated[int, "The second integer to multiply"]
) -> int:
    """Multiply two numbers."""
    return a * b


def add(
    a: Annotated[int, "The first integer to add"],
    b: Annotated[int, "The second integer to add"]
) -> int:
    """Add two numbers."""
    return a + b


def divide(
    a: Annotated[int, "The dividend"],
    b: Annotated[int, "The divisor"]
) -> float:
    """Divide two numbers."""
    return a / b


tools = [multiply, add, divide]


async def run_server():
    credential = DefaultAzureCredential()
    try:
        client = AzureAIAgentClient(
            project_endpoint=ENDPOINT,
            model_deployment_name=MODEL_DEPLOYMENT_NAME,
            credential=credential,
        )
        
        agent = client.create_agent(
            name="CalculatorAgent",
            model=MODEL_DEPLOYMENT_NAME,
            instructions="You are a helpful assistant tasked with performing arithmetic. Use the provided tools to perform calculations.",
            tools=tools,
        )
        
        print("Starting Calculator Agent HTTP Server...")
        await from_agent_framework(agent).run_async()
    finally:
        await credential.close()


def main():
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
```

## Common Pitfalls

### 1. Wrong Client Type
❌ `AzureAIClient` - Does not work with hosted agent deployment  
✅ `AzureAIAgentClient` - Correct client for hosted agents

### 2. Wrong Environment Variables
❌ `AZURE_AI_PROJECT_ENDPOINT` in code  
✅ `FOUNDRY_PROJECT_ENDPOINT` in code (mapped from azd vars in agent.yaml)

### 3. Missing HTTP Server Dependencies
The agent server requires `uvicorn` and `fastapi` even though you don't import them directly.

### 4. Unpinned Dependencies
The Agent Framework is in preview with breaking changes. Always pin versions:
```
agent-framework-azure-ai==1.0.0b260107
```

### 5. Python Version
Use Python 3.11-slim, not 3.12-slim, for better compatibility.

### 6. Missing PORT Environment Variable
Add `ENV PORT=8088` to Dockerfile for health checks.

## Migration Checklist

- [ ] Convert `@tool` functions to `Annotated` parameter style
- [ ] Replace StateGraph with `AzureAIAgentClient.create_agent()`
- [ ] Add async wrapper with `from_agent_framework(agent).run_async()`
- [ ] Create `agent.yaml` with `FOUNDRY_*` environment variables
- [ ] Create `Dockerfile` with Python 3.11-slim and PORT=8088
- [ ] Update `requirements.txt` with pinned versions
- [ ] Create/update `azure.yaml` with `host: azure.ai.agent`
- [ ] Deploy with `azd deploy`
- [ ] Test in Azure AI Foundry playground

## Deployment Commands

```bash
# Initialize azd (first time only)
azd init

# Provision infrastructure
azd provision

# Deploy agent
azd deploy

# View logs (if issues)
azd monitor
```

## References

- [Microsoft Agent Framework Documentation](https://github.com/microsoft/agent-framework)
- [Azure AI Foundry](https://ai.azure.com)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
