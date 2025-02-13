import asyncio
from smartpup import Pup, ToolRegistry
from pydantic import BaseModel

# Define the expected response format as a pydantic model
class WeatherReport(BaseModel):
    temperature: float
    conditions: str
    summary: str
    location: str

async def main():
    # Initialize and get weather tool
    registry = ToolRegistry()
    registry.discover_tools()
    
    # Create weather pup that uses the built-in weather tool
    weather_pup = Pup(
        instructions="You are a weather assistant. Check the weather and provide a structured report.",
        tools=registry.get_tools(["get_current_weather"]),
        json_response=WeatherReport
    )

    # Get weather
    response = await weather_pup.run("What's the weather in Amsterdam?")
    print(f"\nWeather in {response.location}:")
    print(f"Temperature: {response.temperature}°C")
    print(f"Conditions: {response.conditions}")
    print(f"Summary: {response.summary}")

if __name__ == "__main__":
    asyncio.run(main()) 