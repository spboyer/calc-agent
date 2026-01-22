import asyncio
import os
import logging

from typing import Annotated
from azure.identity.aio import DefaultAzureCredential

from agent_framework.azure import AzureAIAgentClient
from azure.ai.agentserver.agentframework import from_agent_framework
from azure.monitor.opentelemetry import configure_azure_monitor
from dotenv import load_dotenv

# Load environment variables (with override for deployed environment)
load_dotenv(override=True)

logger = logging.getLogger(__name__)

if os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"):
    configure_azure_monitor(enable_live_metrics=True, logger_name="__main__")

# Foundry Configuration
ENDPOINT = os.getenv("FOUNDRY_PROJECT_ENDPOINT", "")
MODEL_DEPLOYMENT_NAME = os.getenv("FOUNDRY_MODEL_DEPLOYMENT_NAME", "")


# Define tools
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


def add(
    a: Annotated[int, "The first integer to add"],
    b: Annotated[int, "The second integer to add"]
) -> int:
    """Adds a and b.

    Args:
        a: first int
        b: second int
    """
    return a + b


def divide(
    a: Annotated[int, "The dividend (numerator)"],
    b: Annotated[int, "The divisor (denominator)"]
) -> float:
    """Divide a and b.

    Args:
        a: first int
        b: second int
    """
    return a / b


# Collect all tools
tools = [add, multiply, divide]


async def run_server():
    """Run the calculator agent as an HTTP server."""
    credential = DefaultAzureCredential()
    
    try:
        # Create client using AzureAIAgentClient (same pattern as weather-agent)
        client = AzureAIAgentClient(
            project_endpoint=ENDPOINT,
            model_deployment_name=MODEL_DEPLOYMENT_NAME,
            credential=credential,
        )
        
        # Create agent with function tools
        agent = client.create_agent(
            name="CalculatorAgentAF",
            model=MODEL_DEPLOYMENT_NAME,
            instructions="You are a helpful assistant tasked with performing arithmetic on a set of inputs. Use the provided tools to perform calculations.",
            tools=tools,
        )
        
        logger.info("Starting Calculator Agent HTTP Server...")
        print("Starting Calculator Agent HTTP Server...")
        
        # Run the agent as a hosted agent
        await from_agent_framework(agent).run_async()
    finally:
        await credential.close()


def main():
    """Main entry point for the hosted agent server."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
