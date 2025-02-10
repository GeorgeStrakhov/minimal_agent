import asyncio
from smartpup import Pup, ToolRegistry

async def main():
    # Initialize and get weather tool
    registry = ToolRegistry()
    registry.discover_tools()
    
    # Create weather pup
    weather_pup = Pup(
        system_prompt="You are a weather assistant. Check the weather and report it as a short poem.",
        tools=registry.get_tools(["get_current_weather"])
    )

    # Get weather for one location
    response = await weather_pup.run("What's the weather like in Amsterdam?")
    print(f"Response: {response}")

if __name__ == "__main__":
    asyncio.run(main()) 