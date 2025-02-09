from openai import OpenAI
import os
from dotenv import load_dotenv
from loguru import logger
from agent import Agent
import json
from jsonschema.exceptions import ValidationError
from tools.registry import ToolRegistry
from typing import Any
import asyncio

load_dotenv()

async def run_conversation():
    logger.info("Starting conversation")
    
    # Initialize tool registry
    registry = ToolRegistry()
    registry.discover_tools()
    
    # Get tools and functions
    tools = registry.get_schemas()
    tool_functions = registry.get_tool_functions()
    
    agent = Agent(
        base_url=os.getenv("OPENROUTER_BASE_URL"),
        api_key=os.getenv("OPENROUTER_API_KEY"),
        max_iterations=5
    )

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

    messages = [
        {
            "role": "system",
            "content": """You are a helpful assistant that can check weather information and remember user preferences. 
            
            Follow these steps in order:
            1. First check if there's a last_city in memory using the recall tool
            2. If found, use that city, otherwise respond that no previous city was found
            3. Get the current weather for the city
            4. ALWAYS use the remember tool to save the last requested city with key="last_city"
            5. Return the weather information as JSON
            
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
            "content": "What's the current weather in London?"
        }
    ]

    try:
        response = await agent.run(messages, tools, tool_functions, json_response=json_schema)
        print("\nAssistant:", json.dumps(response, indent=2))
        
    except ValueError as e:
        print(f"Error: {e}")
    except ValidationError as e:
        print(f"JSON validation error: {e}")

if __name__ == "__main__":
    logger.info("Starting weather conversation application")
    asyncio.run(run_conversation())