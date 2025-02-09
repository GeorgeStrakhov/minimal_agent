from openai import OpenAI
import os
from dotenv import load_dotenv
from loguru import logger
from agent import Agent
import json
from jsonschema import validate as validate_json
from jsonschema.exceptions import ValidationError

load_dotenv()

def get_city_coordinates(city: str) -> str:
    """Mock function to return city coordinates"""
    # This is just a mock implementation
    coordinates = {
        "boston": {"lat": 42.3601, "lon": -71.0589},
        "new york": {"lat": 40.7128, "lon": -74.0060},
        "san francisco": {"lat": 37.7749, "lon": -122.4194}
    }
    city_key = city.lower()
    if city_key in coordinates:
        coords = coordinates[city_key]
        return f"Coordinates for {city}: {coords['lat']}, {coords['lon']}"
    return f"Could not find coordinates for {city}"

def get_current_weather(location: str, coordinates: str = None, unit: str = "celsius") -> str:
    """Mock function to return weather data"""
    # This is just a mock implementation
    if coordinates:
        return f"The weather at coordinates {coordinates} is 32°{'C' if unit == 'celsius' else 'F'} and raining"
    return f"The weather in {location} is 32°{'C' if unit == 'celsius' else 'F'} and raining"

def run_conversation():
    logger.info("Starting conversation")
    
    agent = Agent(
        base_url=os.getenv("OPENROUTER_BASE_URL"),
        api_key=os.getenv("OPENROUTER_API_KEY"),
        max_iterations=5
    )

    messages = [
        {
            "role": "system",
            "content": """You are a helpful assistant that can check weather information. You MUST follow these exact steps:

1. FIRST, you must call get_city_coordinates to get the exact coordinates
2. THEN, you must call get_current_weather with those coordinates
3. ONLY AFTER getting real data from both tools, return a JSON object with this structure:
{
    "location": "city name",
    "coordinates": {
        "latitude": number,
        "longitude": number
    },
    "temperature": {
        "value": number,
        "unit": string
    },
    "conditions": string
}

DO NOT make up or guess any values - you must get real data using the tools."""
        },
        {
            "role": "user",
            "content": "What's the current weather in Boston? Please include the coordinates in your response."
        }
    ]

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

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_city_coordinates",
                "description": "Get the coordinates (latitude and longitude) for a given city",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "The city name, e.g. Boston"
                        }
                    },
                    "required": ["city"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather for a location, preferably using coordinates",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city name, e.g. Boston"
                        },
                        "coordinates": {
                            "type": "string",
                            "description": "The latitude and longitude coordinates"
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"]
                        }
                    },
                    "required": ["location"]
                }
            }
        }
    ]

    # Map of tool names to their functions
    tool_functions = {
        "get_city_coordinates": get_city_coordinates,
        "get_current_weather": get_current_weather
    }

    try:
        response = agent.run(messages, tools, tool_functions, json_response=json_schema)
        print("Assistant:", json.dumps(response, indent=2))
    except ValueError as e:
        print(f"Error: {e}")
    except ValidationError as e:
        print(f"JSON validation error: {e}")

if __name__ == "__main__":
    logger.info("Starting weather conversation application")
    run_conversation()