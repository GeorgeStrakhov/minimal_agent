from tools.registry import ToolRegistry
from pup import Pup
import asyncio
from loguru import logger
import json

async def main():
    # Initialize tool registry
    registry = ToolRegistry()
    registry.discover_tools()
    
    # Get tools and functions
    tools = registry.get_schemas()
    tool_functions = registry.get_tool_functions()
    
    # Define the expected JSON response schema
    json_schema = {
        "type": "object",
        "properties": {
            "location": {"type": "string"},
            "coordinates": {
                "type": "object",
                "properties": {
                    "latitude": {"type": "number"},
                    "longitude": {"type": "number"}
                },
                "required": ["latitude", "longitude"]
            },
            "temperature": {
                "type": "object",
                "properties": {
                    "value": {"type": "number"},
                    "unit": {"type": "string"}
                },
                "required": ["value", "unit"]
            },
            "conditions": {"type": "string"}
        },
        "required": ["location", "coordinates", "temperature", "conditions"]
    }

    # Basic pup without tools
    zen_pup = Pup(
        system_prompt="""You are a zen master, you always respond with a koan and nothing else."""
    )

    # Weather pup with tools configured at init
    weather_pup = Pup(
        system_prompt="""You are a weather assistant, you always respond with the current weather in the specified city using available tools. Don't forget to update the memory about the last city that the user has asked for.""",
        json_response=json_schema,
        tools=tools,
        tool_functions=tool_functions
    )

    try:
        # Run conversations
        response = await zen_pup.run(
            "What's the current weather in Dubai?"
        )
        print("\nAssistant:", json.dumps(response, indent=2))

        response = await weather_pup.run(
            "What's the current weather in Chicago?"
        )
        print("\nAssistant:", json.dumps(response, indent=2))
        
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    logger.info("Starting weather conversation application")
    asyncio.run(main())