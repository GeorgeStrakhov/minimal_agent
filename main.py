from openai import OpenAI
import os
from dotenv import load_dotenv
from loguru import logger
from agent import Agent
import json
from jsonschema import validate as validate_json
from jsonschema.exceptions import ValidationError

load_dotenv()

def get_current_weather(location: str, unit: str = "celsius") -> str:
    """Mock function to return weather data"""
    # This is just a mock implementation
    return f"The weather in {location} is 32°{'C' if unit == 'celsius' else 'F'} and raining"

def run_conversation():
    logger.info("Starting conversation")
    
    # Initialize the agent with custom max_iterations
    agent = Agent(
        base_url=os.getenv("OPENROUTER_BASE_URL"),
        api_key=os.getenv("OPENROUTER_API_KEY"),
        max_iterations=5  # Custom limit
    )

    # Example of requesting a JSON response
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that can check weather information."
        },
        {
            "role": "user",
            "content": "What is the weather like in Boston? Return the information in JSON format."
        }
    ]

    # Define the expected JSON response schema
    json_schema = {
        "type": "object",
        "properties": {
            "location": {"type": "string"},
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
        "required": ["location", "temperature", "conditions"]
    }

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA"
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
    logger.debug("Tools configuration: {}", tools)

    # Map of tool names to their functions
    tool_functions = {
        "get_current_weather": get_current_weather
    }

    try:
        # Run the conversation with JSON validation
        response = agent.run(messages, tools, tool_functions, json_response=json_schema)
        print("Assistant:", json.dumps(response, indent=2))
    except ValueError as e:
        print(f"Error: {e}")
    except ValidationError as e:
        print(f"JSON validation error: {e}")

if __name__ == "__main__":
    logger.info("Starting weather conversation application")
    run_conversation()