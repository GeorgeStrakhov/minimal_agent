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

    # Create a weather pup with specific behavior
    weather_pup = Pup(
        system_prompt="""You are a helpful assistant that can check weather information and remember user preferences. 

        Follow these steps in order:
        1. First check if there's a last_city in memory using the recall tool
        2. If no previous city is found AND the user hasn't specified a city, respond with: "No previous city found. Please specify a city."
        3. Get the current weather for either:
           - The city from memory (if found)
           - OR the city specified in the user's message
        4. ALWAYS use the remember tool to save the city name when providing the final response
        5. Return ONLY the weather information as JSON, do not include the schema itself
        
        Important notes:
        - Always include actual coordinates from the weather API response
        - Never return null or empty values
        - Remove any fields that don't have valid data
        - Format numbers to 2 decimal places
        
        Example response format:
        {
            "location": "New York",
            "coordinates": {
                "latitude": 40.71,
                "longitude": -74.01
            },
            "temperature": {
                "value": 20.50,
                "unit": "celsius"
            },
            "conditions": "sunny"
        }
        
        Important: Only return JSON when you have actual weather data to report""",
        json_response=json_schema
    )

    try:
        # Run the conversation with just the user message
        response = await weather_pup.run(
            "What's the current weather in Dubai?",
            tools=tools,
            tool_functions=tool_functions
        )
        print("\nAssistant:", json.dumps(response, indent=2))
        
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    logger.info("Starting weather conversation application")
    asyncio.run(main())