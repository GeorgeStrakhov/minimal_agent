from openai import OpenAI
import os
from dotenv import load_dotenv
from loguru import logger
from agent import Agent

load_dotenv()

def get_current_weather(location: str, unit: str = "celsius") -> str:
    """Mock function to return weather data"""
    # This is just a mock implementation
    return f"The weather in {location} is 32°{'C' if unit == 'celsius' else 'F'} and raining"

def run_conversation():
    logger.info("Starting conversation")
    
    # Initialize the agent
    agent = Agent(
        base_url=os.getenv("OPENROUTER_BASE_URL"),
        api_key=os.getenv("OPENROUTER_API_KEY")
    )

    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that can check weather information. But once you have it - turn it into a haiku."
        },
        {
            "role": "user",
            "content": "What is the weather like in Boston?"
        }
    ]
    logger.debug("Initial messages: {}", messages)

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

    # Run the conversation
    response = agent.run(messages, tools, tool_functions)
    print("Assistant:", response)

if __name__ == "__main__":
    logger.info("Starting weather conversation application")
    run_conversation()