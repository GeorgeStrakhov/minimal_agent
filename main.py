from tools.registry import ToolRegistry
from pup import Pup
import asyncio
from loguru import logger
import json
from errors import PupError
from pydantic import BaseModel, Field
from typing import Optional

class WeatherResponse(BaseModel):
    location: str = Field(..., description="Name of the location")
    coordinates: dict = Field(..., description="Geographic coordinates", example={
        "latitude": 48.8566,
        "longitude": 2.3522
    })
    temperature: dict = Field(..., description="Temperature information", example={
        "value": 22.5,
        "unit": "celsius"
    })
    conditions: str = Field(..., description="Weather conditions description")

async def main():
    # Initialize tool registry
    registry = ToolRegistry()
    registry.discover_tools()
    
    # Get tools and functions
    tools = registry.get_schemas()
    tool_functions = registry.get_tool_functions()
    
    # Basic pup without tools
    zen_pup = Pup(
        system_prompt="""You are a zen master. you only respond in zen koans to everything"""
    )

    # Weather pup with tools configured at init
    weather_pup = Pup(
        system_prompt="""You are a weather assistant that provides current weather information for cities to users. And you use memory tool to save the last city that the user has asked for in last_city""",
        json_response=WeatherResponse,
        model="anthropic/claude-3.5-sonnet",
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
            "What's the current weather in Mumbai?"
        )
        print("\nAssistant:", json.dumps(response, indent=2))
        
    except PupError as e:
        if e.type == PupError.COGNITIVE:
            logger.error("Pup was confused: {} ({})", e.message, e.subtype)
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