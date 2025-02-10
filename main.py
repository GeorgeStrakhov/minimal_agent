from tools.registry import ToolRegistry
from tools import BaseTool
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

class MockWeatherTool(BaseTool):
    name = "get_weather"
    description = "Get mock weather for a location"
    
    async def execute(
        self,
        location: str,
        unit: str = "celsius"
    ) -> str:
        """
        Get mock weather for a location
        
        Args:
            location: The location to get weather for
            unit: Temperature unit (celsius/fahrenheit)
        """
        return f"gmbasdfjhgasdf tkkjahsdf tool broken asdlfkjahsdlkjh !"

async def main():
    # Initialize tool registry
    registry = ToolRegistry()
    
    # Register your mock tool directly
    registry.register_tool(MockWeatherTool)
    
    # Get the mock weather tool
    weather_tools = registry.get_tools(["get_weather"])
    
    # Create weather pup
    weather_pup = Pup(
        system_prompt="""You are a weather assistant. Use the get_weather tool to check the weather.""",
        tools=weather_tools
    )

    try:
        response = await weather_pup.run(
            "What's the weather like in Paris?"
        )
        print("\nWeather:", response)
        
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
    logger.info("Starting weather test")
    asyncio.run(main())