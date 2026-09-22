"""
MCP Weather Client

Connects to the weather MCP server.
Gemini decides whether to call get_current_weather().
The weather result is then sent back to Gemini for a final summary.
"""

import asyncio
import json
import os
import sys

from google import genai
from mcp import Client, StdioServerParameters


# Gemini tool declaration
WEATHER_TOOL = {
    "type": "function",
    "name": "get_current_weather",
    "description": (
        "Gets the current real-time weather information for a "
        "specified city or location."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": (
                    "The city or location for which current weather "
                    "information is required."
                )
            }
        },
        "required": ["location"]
    }
}


def get_result_text(result):
    """
    Extract text from the MCP tool result.

    Args:
        result: MCP CallToolResult object.

    Returns:
        Combined text returned by the MCP tool.
    """

    texts = []

    for item in result.content:
        if hasattr(item, "text"):
            texts.append(item.text)

    return "\n".join(texts)


async def main():
    """
    Run the Weather Data Dashboard client.
    """

    print("\n======================================")
    print("   Weather Data Dashboard")
    print("   MCP + Gemini + wttr.in")
    print("======================================\n")

    # Read Gemini API key from environment
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("ERROR: GEMINI_API_KEY is not set.")
        print()
        print("Run this in PowerShell:")
        print('$env:GEMINI_API_KEY="YOUR_NEW_KEY"')
        return

    # Create Gemini client
    gemini = genai.Client(api_key=api_key)

    # Start the weather MCP server
    server_parameters = StdioServerParameters(
        command=sys.executable,
        args=["weather_server.py"]
    )

    async with Client(server_parameters) as mcp_client:

        # Discover MCP tools
        tools_result = await mcp_client.list_tools()

        print("Connected to Weather MCP server.")
        print("\nAvailable MCP tools:")

        for tool in tools_result.tools:
            print(f" - {tool.name}")

        print("\n--------------------------------------")

        while True:

            user_input = input("\nYou: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit"]:
                print("\nGoodbye!")
                break

            print("\nGemini is deciding which MCP tool to use...")

            try:
                # First Gemini interaction:
                # Gemini decides whether to call the weather tool.
                interaction = gemini.interactions.create(
                    model="gemini-3.6-flash",
                    input=user_input,
                    system_instruction=(
                        "You are a weather assistant. "
                        "When the user asks about current weather, "
                        "always use the get_current_weather tool. "
                        "Do not invent current weather information."
                    ),
                    tools=[WEATHER_TOOL]
                )

            except Exception as e:
                print("\nGemini API Error:")
                print(e)
                continue

            # Find Gemini's function call
            function_call = None

            for step in interaction.steps:
                if step.type == "function_call":
                    function_call = step
                    break

            if function_call is None:
                print("\nGemini did not select the weather tool.")

                if hasattr(interaction, "output_text"):
                    print("Gemini:", interaction.output_text)

                continue

            # Display the tool-selection step
            print(f"\nGemini selected: {function_call.name}")
            print(f"Arguments: {function_call.arguments}")

            # Make sure the correct tool was selected
            if function_call.name != "get_current_weather":
                print("\nUnexpected tool selected.")
                continue

            try:
                # Call the MCP weather tool
                result = await mcp_client.call_tool(
                    "get_current_weather",
                    arguments=function_call.arguments
                )

                weather_data = get_result_text(result)

                print("\nMCP Result:")
                print(weather_data)

            except Exception as e:
                print("\nMCP Error:")
                print(e)
                continue

            print("\nGemini is summarizing the weather...")

            try:
                # Send MCP result back to Gemini
                final_interaction = gemini.interactions.create(
                    model="gemini-3.6-flash",
                    previous_interaction_id=interaction.id,
                    input=[
                        {
                            "type": "function_result",
                            "name": function_call.name,
                            "call_id": function_call.id,
                            "result": [
                                {
                                    "type": "text",
                                    "text": weather_data
                                }
                            ]
                        }
                    ]
                )

                print("\nFinal Answer:")
                print(final_interaction.output_text)

            except Exception as e:
                print("\nGemini Final Response Error:")
                print(e)


if __name__ == "__main__":
    asyncio.run(main()) 