from openai import OpenAI
import os
import json
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

def get_current_weather(location: str, unit: str = "celsius") -> str:
    """Mock function to return weather data"""
    # This is just a mock implementation
    return f"The weather in {location} is 22°{'C' if unit == 'celsius' else 'F'} and partly cloudy"

def run_conversation():
    logger.info("Starting conversation")
    client = OpenAI(
        base_url=os.getenv("OPENROUTER_BASE_URL"),
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )
    logger.debug("OpenAI client initialized with OpenRouter configuration")

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

    while True:
        logger.info("Making API call to OpenRouter")
        completion = client.chat.completions.create(
            model="google/gemini-2.0-flash-001",
            messages=messages,
            tools=tools
        )
        logger.debug("Received response: {}", completion)

        response_message = completion.choices[0].message

        # If there's no tool calls, we can return the response to the user
        if not response_message.tool_calls:
            logger.info("No tool calls, returning response to user")
            print("Assistant:", response_message.content)
            break

        # Handle tool calls
        logger.info("Processing tool calls")
        for tool_call in response_message.tool_calls:
            if tool_call.function.name == "get_current_weather":
                logger.debug("Handling weather function call: {}", tool_call)
                # Parse the arguments
                function_args = json.loads(tool_call.function.arguments)
                logger.debug("Function arguments: {}", function_args)
                
                # Call the function
                function_response = get_current_weather(
                    location=function_args.get("location"),
                    unit=function_args.get("unit", "celsius")
                )
                logger.debug("Weather function response: {}", function_response)

                # Append the function call and result to messages
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [tool_call]
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": function_response
                })
                logger.debug("Updated messages: {}", messages)

            else:
                logger.warning("Unknown tool call received: {}", tool_call)
                print("Unknown tool call:", tool_call)
                break

if __name__ == "__main__":
    logger.info("Starting weather conversation application")
    run_conversation()