from openai import OpenAI
import os
from typing import List, Dict, Any, Callable, Optional, Union
import json
from loguru import logger
from jsonschema import validate as validate_json
from jsonschema.exceptions import ValidationError
import asyncio
from typing import Awaitable
from dotenv import load_dotenv

load_dotenv()

class Pup:
    def __init__(
        self,
        system_prompt: str,
        json_response: Optional[Dict[str, Any]] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: str = "google/gemini-2.0-flash-001",
        max_iterations: int = 10
    ):
        """
        Initialize a new Pup.
        
        Args:
            system_prompt: The system prompt that defines the pup's behavior
            json_response: Optional schema for validating JSON responses
            base_url: OpenAI API base URL (defaults to OPENROUTER_BASE_URL from env)
            api_key: OpenAI API key (defaults to OPENROUTER_API_KEY from env)
            model: Model to use for completions
            max_iterations: Maximum number of tool call iterations
        """
        self.base_url = base_url or os.getenv("OPENROUTER_BASE_URL")
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        
        if not self.base_url or not self.api_key:
            raise ValueError("Must provide base_url and api_key either directly or via environment variables")
            
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )
        
        # Store the system prompt and JSON schema
        self.system_prompt = system_prompt
        if json_response:
            self.system_prompt += "\n\nYour final response must be a valid JSON object with this exact structure:\n" + json.dumps(json_response, indent=2)
        self.json_response = json_response
        
        self.model = model
        self.max_iterations = max_iterations
        logger.debug("Pup initialized with model: {} and max_iterations: {}", 
                    model, max_iterations)

    def _clean_json_response(self, content: str) -> Dict[str, Any]:
        """
        Clean up the response content and return a Python dict.
        """
        # Find JSON content between triple backticks if present
        if '```' in content:
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
        
        # Remove any non-JSON text before or after the JSON object
        content = content.strip()
        
        # Find the outermost JSON object
        first_brace = content.find('{')
        if first_brace == -1:
            raise ValueError("No JSON object found in response")
            
        brace_count = 0
        for i, char in enumerate(content[first_brace:], first_brace):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    content = content[first_brace:i+1]
                    break
        
        # Parse the JSON
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            raise ValueError("Response is not a JSON object")
            
        # Remove any schema-related fields
        if "type" in parsed and "properties" in parsed:
            parsed = {k: v for k, v in parsed.items() 
                     if k not in ["type", "properties", "required"]}
            
        # Clean up any null values in nested objects
        def clean_nulls(obj):
            if isinstance(obj, dict):
                return {k: clean_nulls(v) for k, v in obj.items() 
                       if v is not None and v != {}}
            return obj
            
        return clean_nulls(parsed)

    async def run(
        self,
        user_message: str,
        tools: List[Dict[str, Any]],
        tool_functions: Dict[str, Callable]
    ) -> Union[str, Dict[str, Any]]:
        """
        Run a conversation with the given user message and tools.
        
        Args:
            user_message: The user's message to respond to
            tools: List of tool schemas
            tool_functions: Dictionary of tool functions
            
        Returns:
            The final response, either as a string or JSON object
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        logger.debug("Starting conversation with user message: {}", user_message)
        logger.debug("Available tools: {}", list(tool_functions.keys()))

        iterations = 0
        while iterations < self.max_iterations:
            iterations += 1
            logger.info(f"Starting iteration {iterations}/{self.max_iterations}")
            
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools
            )
            
            response_message = completion.choices[0].message
            logger.debug("Model response: {}", response_message)

            # First, check if we have a valid response content
            if response_message.content and response_message.content.strip():
                logger.info("Processing response content")
                content = response_message.content.strip()
                
                if self.json_response:
                    try:
                        # Parse and clean the JSON response
                        cleaned_data = self._clean_json_response(content)
                        # Validate against schema
                        validate_json(instance=cleaned_data, schema=self.json_response)
                        return cleaned_data
                    except (json.JSONDecodeError, ValidationError) as e:
                        logger.error("Response validation failed: {}", e)
                        if not response_message.tool_calls:
                            return content
                    except Exception as e:
                        logger.error("Content cleaning failed: {}", e)
                        if not response_message.tool_calls:
                            return content
                else:
                    return content

            # Then, handle any tool calls
            if response_message.tool_calls:
                logger.info("Processing tool calls")
                tool_results = []
                
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    
                    if function_name not in tool_functions:
                        logger.warning("Unknown tool call received: {}", function_name)
                        raise ValueError(f"Unknown tool: {function_name}")

                    logger.debug("Handling function call: {}", tool_call)
                    function_args = json.loads(tool_call.function.arguments)
                    logger.debug("Function arguments: {}", function_args)
                    
                    function = tool_functions[function_name]
                    function_response = await function(**function_args)
                    logger.debug("Function response: {}", function_response)
                    
                    tool_results.append({
                        "tool_call_id": tool_call.id,
                        "function_response": function_response
                    })

                # Add all tool responses at once
                messages.extend([
                    {
                        "role": "assistant",
                        "content": response_message.content,
                        "tool_calls": response_message.tool_calls
                    },
                    *[{
                        "role": "tool",
                        "tool_call_id": result["tool_call_id"],
                        "content": result["function_response"]
                    } for result in tool_results]
                ])
                # logger.debug("Updated messages: {}", messages)
                
                # Continue the conversation if we have tool calls
                continue

            # If we reach here, we have no more tool calls
            if response_message.content and response_message.content.strip():
                logger.error("No valid response or tool calls received")
                raise ValueError("Model must provide either a valid response or tool calls")
                
            return response_message.content

        raise ValueError(f"Max iterations ({self.max_iterations}) reached without final response") 