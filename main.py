from openai import OpenAI
import os
from dotenv import load_dotenv
from loguru import logger
from agent import Agent
import json
from jsonschema.exceptions import ValidationError
from memory import FileMemory
from typing import Any

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
        return f"The weather at coordinates {coordinates} is 2°{'C' if unit == 'celsius' else 'F'} and partly cloudy"
    return f"The weather in {location} is 2°{'C' if unit == 'celsius' else 'F'} and partly cloudy"

def run_conversation():
    logger.info("Starting conversation")
    
    # Initialize memory
    memory = FileMemory()
    
    agent = Agent(
        base_url=os.getenv("OPENROUTER_BASE_URL"),
        api_key=os.getenv("OPENROUTER_API_KEY"),
        max_iterations=5
    )

    messages = [
        {
            "role": "system",
            "content": """You are a helpful assistant that can check weather information and remember user preferences. 
            
            Follow these steps in order:
            1. Get the city coordinates
            2. Get the current weather
            3. ALWAYS use the remember tool to save the last requested city with key="last_city"
            4. Return the weather information as JSON
            
            Your final response must be a valid JSON object with these exact fields:
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
            
            Do not include the schema definition in your response, just the actual values.
            
            Important: You must use the remember tool to save the city name before providing the final response."""
        },
        {
            "role": "user",
            "content": "What's the current weather in in the last city I asked for (use memory for last_city)? Please include the coordinates in your response."
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

    def remember(key: str, value: Any) -> str:
        """Tool function to save information to memory"""
        return memory.save(key, value)

    def recall(key: str) -> str:
        """Tool function to recall information from memory"""
        value = memory.get(key)
        return f"Remembered value for {key}: {value}" if value is not None else f"No memory found for {key}"

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
                        "location": {"type": "string"},
                        "coordinates": {"type": "string"},
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"]
                        }
                    },
                    "required": ["location"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "remember",
                "description": "Save information to memory for future use",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "key": {
                            "type": "string",
                            "description": "The key to store the value under"
                        },
                        "value": {
                            "type": "string",
                            "description": "The value to remember"
                        }
                    },
                    "required": ["key", "value"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "recall",
                "description": "Recall information from memory",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "key": {
                            "type": "string",
                            "description": "The key to recall the value for"
                        }
                    },
                    "required": ["key"]
                }
            }
        }
    ]

    # Map of tool names to their functions
    tool_functions = {
        "get_city_coordinates": get_city_coordinates,
        "get_current_weather": get_current_weather,
        "remember": remember,
        "recall": recall
    }

    try:
        response = agent.run(messages, tools, tool_functions, json_response=json_schema)
        print("Assistant:", json.dumps(response, indent=2))
        
        # Print the current memory contents
        print("\nCurrent memory contents:")
        print(json.dumps(memory.get_all(), indent=2))
    except ValueError as e:
        print(f"Error: {e}")
    except ValidationError as e:
        print(f"JSON validation error: {e}")

if __name__ == "__main__":
    logger.info("Starting weather conversation application")
    run_conversation()