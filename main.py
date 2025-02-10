from tools.registry import ToolRegistry
from pup import Pup
import asyncio
from loguru import logger
import json
from errors import PupError

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
        system_prompt="""You are a weather assistant that provides current weather information for cities to users. And you use memory tool to save the last city that the user has asked for.""",
        json_response=json_schema,
        tools=tools,
        tool_functions=tool_functions
    )

    try:
        # Run conversations
        response = await zen_pup.run(
            "What's the current weather, baby pup?"
        )
        print("\nAssistant:", json.dumps(response, indent=2))

        response = await weather_pup.run(
            "What's the current weather in Paris?"
        )
        print("\nAssistant:", json.dumps(response, indent=2))
        
    except PupError as e:
        if e.type == PupError.COGNITIVE:
            logger.warning("Pup was confused: {} ({})", e.message, e.subtype)
        elif e.subtype == PupError.INVALID_JSON:
            logger.error("Pup didn't return valid JSON: {}", e.message)
        elif e.subtype == PupError.SCHEMA_VIOLATION:
            logger.error("Pup's JSON didn't match schema: {}", e.message)
        else:
            logger.error("Technical error: {} ({})", e.message, e.subtype)
            
        if e.details:
            logger.debug("Error details: {}", e.details)
    except Exception as e:
        logger.error("Unexpected error: {}", str(e))

if __name__ == "__main__":
    logger.info("Starting weather conversation application")
    asyncio.run(main())