import asyncio
import os
import sys

from google import genai
from mcp import Client, StdioServerParameters


# ---------------------------------------------------------
# MCP tool definitions for Gemini
# ---------------------------------------------------------

SAVE_NOTE_TOOL = {
    "type": "function",
    "name": "save_note",
    "description": (
        "Save information when the user wants to remember, "
        "store, or record something."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "The information that should be saved."
            },
            "tags": {
                "type": "string",
                "description": "Comma-separated tags for the note."
            }
        },
        "required": ["content", "tags"]
    }
}


SEARCH_NOTES_TOOL = {
    "type": "function",
    "name": "search_notes",
    "description": (
        "Search saved notes when the user asks about something "
        "they previously said, saved, or remembered."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The information or keywords to search for."
            }
        },
        "required": ["query"]
    }
}


# ---------------------------------------------------------
# Extract text from MCP result
# ---------------------------------------------------------

def get_result_text(result):
    texts = []

    for item in result.content:
        if hasattr(item, "text"):
            texts.append(item.text)

    return "\n".join(texts)


# ---------------------------------------------------------
# Main program
# ---------------------------------------------------------

async def main():

    print("\n======================================")
    print(" Personal Assistant - MCP + Gemini")
    print("======================================\n")

    # Check API key
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("ERROR: GEMINI_API_KEY is not set.")
        print()
        print("Run:")
        print('$env:GEMINI_API_KEY="YOUR_NEW_KEY"')
        return

    # Create Gemini client
    gemini = genai.Client(api_key=api_key)

    # Start MCP server using the same Python interpreter
    server_parameters = StdioServerParameters(
        command=sys.executable,
        args=["server.py"]
    )

    # Connect to MCP server
    async with Client(server_parameters) as mcp_client:

        # Get MCP tools
        tools_result = await mcp_client.list_tools()

        print("Connected to MCP server.")
        print("\nAvailable MCP tools:")

        for tool in tools_result.tools:
            print(f" - {tool.name}")

        print("\n--------------------------------------")

        # -------------------------------------------------
        # Interactive assistant
        # -------------------------------------------------

        while True:

            user_input = input("\nYou: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit"]:
                print("\nGoodbye!")
                break

            print("\nGemini is deciding which MCP tool to use...")

            try:
                # Ask Gemini to select save_note or search_notes
                interaction = gemini.interactions.create(
                    model="gemini-3.6-flash",
                    input=user_input,
                    system_instruction=(
                        "You are a personal memory assistant. "
                        "Use save_note when the user wants to remember, "
                        "save, store, or record information. "
                        "Use search_notes when the user asks about "
                        "something they previously said or stored. "
                        "Always use one of these tools for memory operations."
                    ),
                    tools=[
                        SAVE_NOTE_TOOL,
                        SEARCH_NOTES_TOOL
                    ]
                )

            except Exception as e:
                print("\nGemini API Error:")
                print(e)
                continue

            # -------------------------------------------------
            # Find function call
            # -------------------------------------------------

            function_call = None

            for step in interaction.steps:
                if step.type == "function_call":
                    function_call = step
                    break

            if function_call is None:
                print("\nGemini did not select an MCP tool.")

                if hasattr(interaction, "output_text"):
                    print("Gemini:", interaction.output_text)

                continue

            tool_name = function_call.name
            arguments = function_call.arguments

            print(f"Gemini selected: {tool_name}")
            print(f"Arguments: {arguments}")

            # -------------------------------------------------
            # Execute selected MCP tool
            # -------------------------------------------------

            if tool_name == "save_note":

                result = await mcp_client.call_tool(
                    "save_note",
                    arguments=arguments
                )

                print("\nMCP Result:")
                print(get_result_text(result))

            elif tool_name == "search_notes":

                result = await mcp_client.call_tool(
                    "search_notes",
                    arguments=arguments
                )

                print("\nMCP Result:")
                print(get_result_text(result))

            else:

                print(f"\nUnknown tool selected: {tool_name}")


# ---------------------------------------------------------
# Program entry point
# ---------------------------------------------------------

if __name__ == "__main__":
    asyncio.run(main())