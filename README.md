# Calculator Agent - Microsoft Agent Framework Sample

A sample calculator agent built with Microsoft Agent Framework, demonstrating how to deploy a hosted agent on Azure using Azure Developer CLI (azd).

## Overview

This agent provides arithmetic calculation capabilities (add, multiply, divide) using the Microsoft Agent Framework and deploys as a hosted agent on Azure AI Foundry.

### Features

- **Function Tools**: Add, multiply, and divide operations exposed as agent tools
- **Hosted Agent Deployment**: Runs as a containerized agent on Azure AI Foundry
- **Azure Developer CLI**: Infrastructure-as-code deployment with `azd`

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Azure AI Foundry                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Calculator Agent (Container)            │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │    add()    │  │  multiply() │  │  divide()   │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
│                              │                              │
│                              ▼                              │
│                    ┌─────────────────┐                     │
│                    │   gpt-4o-mini   │                     │
│                    └─────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

- [Azure Developer CLI (azd)](https://aka.ms/install-azd)
- Azure subscription with AI Foundry access
- Python 3.11+

## Quick Start

1. **Clone and initialize:**
   ```bash
   git clone https://github.com/spboyer/calc-agent.git
   cd calc-agent
   azd auth login
   ```

2. **Provision infrastructure:**
   ```bash
   azd provision
   ```

3. **Deploy the agent:**
   ```bash
   azd deploy
   ```

4. **Test in Azure AI Foundry Playground** - The deployment output includes a link to the agent playground.

## Project Structure

```
calc-agent/
├── src/
│   └── CalculatorAgent/
│       ├── main.py           # Agent implementation
│       ├── agent.yaml        # Agent configuration
│       ├── requirements.txt  # Python dependencies
│       └── Dockerfile        # Container definition
├── infra/                    # Bicep infrastructure
├── azure.yaml                # azd service configuration
└── LANGGRAPH_TO_AGENT_FRAMEWORK_GUIDE.md  # Migration guide
```

## Agent Implementation

The agent uses `AzureAIAgentClient` to create a hosted agent with function tools:

```python
from agent_framework.azure import AzureAIAgentClient
from azure.ai.agentserver.agentframework import from_agent_framework

client = AzureAIAgentClient(
    project_endpoint=ENDPOINT,
    model_deployment_name=MODEL_DEPLOYMENT_NAME,
    credential=credential,
)

agent = client.create_agent(
    name="CalculatorAgentAF",
    model=MODEL_DEPLOYMENT_NAME,
    instructions="You are a helpful assistant...",
    tools=[add, multiply, divide],
)

await from_agent_framework(agent).run_async()
```

## Key Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `agent-framework-azure-ai` | 1.0.0b260107 | Agent Framework SDK |
| `azure-ai-agentserver-agentframework` | latest | HTTP server for hosted agents |
| `uvicorn` / `fastapi` | latest | Web server (required by agent server) |

## Environment Variables

The agent expects these environment variables (configured in `agent.yaml`):

| Variable | Description |
|----------|-------------|
| `FOUNDRY_PROJECT_ENDPOINT` | Azure AI Foundry project endpoint |
| `FOUNDRY_MODEL_DEPLOYMENT_NAME` | Model deployment name (e.g., gpt-4o-mini) |

## Migration from LangGraph

This sample was migrated from LangGraph. See [LANGGRAPH_TO_AGENT_FRAMEWORK_GUIDE.md](./LANGGRAPH_TO_AGENT_FRAMEWORK_GUIDE.md) for a complete migration guide including:

- Tool conversion patterns
- Client setup differences
- Deployment configuration
- Common pitfalls

## Cleanup

```bash
azd down
```

## Resources

- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-foundry)
- [Azure Developer CLI](https://learn.microsoft.com/azure/developer/azure-developer-cli/)

## License

[MIT](LICENSE.md)
