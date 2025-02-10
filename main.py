from loguru import logger
import asyncio
from pydantic import BaseModel, Field

from smartpup import Pup, ToolRegistry
from smartpup.config import configure

# Configure SmartPup with defaults (can also use environment variables)
configure(
    default_model="openai/gpt-4o-mini",
    max_iterations=10
)

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
    registry.discover_tools()  # Will find built-in tools
    
    # Get weather and memory tools
    tools = registry.get_tools(["get_current_weather", "remember"])
    
    # Create weather pup
    weather_pup = Pup(
        system_prompt="""You are a weather assistant. Use the weather tool to check 
        the weather and report it back to the user as a little poem. You MUST use 
        the tool first. Then use the memory tool (remember) to remember the city 
        and the weather for later use.""",
        tools=tools
    )

    try:
        response = await weather_pup.run(
            "What's the weather like in Paris?"
        )
        print("\nWeather:", response)
        
    except Exception as e:
        logger.error("Error: {}", str(e))
        if hasattr(e, 'details'):
            logger.debug("Error details: {}", e.details)

if __name__ == "__main__":
    logger.info("Starting weather test")
    asyncio.run(main())