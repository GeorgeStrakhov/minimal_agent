from openai import OpenAI
import os
from typing import List, Dict, Any, Callable, Optional, Union, Type, get_type_hints
import json
from loguru import logger
from jsonschema import validate as validate_json
from jsonschema.exceptions import ValidationError
import asyncio
from typing import Awaitable
from dotenv import load_dotenv
from .errors import PupError
from .config import config
from pydantic import BaseModel, create_model
from .tools.base import BaseTool
from .tools.registry import ToolRegistry

load_dotenv()

class Pup:
    def __init__(
        self,
        instructions: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        json_response: Optional[Union[Dict[str, Any], Type[BaseModel]]] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_iterations: Optional[int] = None,
        tools: Optional[Dict[str, Dict[str, Any]]] = None,
        temperature: Optional[float] = 0.7
    ):
        """
        Initialize a new Pup.
        
        Args:
            instructions: The system prompt that defines the pup's behavior
            name: Optional name for the pup
            description: Optional description for the pup
            json_response: Optional schema for validating JSON responses
            base_url: OpenAI API base URL (defaults to config or env OPENROUTER_BASE_URL)
            api_key: OpenAI API key (defaults to config or env OPENROUTER_API_KEY)
            model: Model to use for completions (defaults to config default_model)
            max_iterations: Maximum number of tool call iterations (defaults to config max_iterations)
            tools: Optional dictionary of tool configurations containing schemas and functions
            temperature: Optional temperature setting for model responses (0.0 to 2.0)
        """
        self.name = name
        self.description = description
        self.base_url = base_url or config.openrouter_base_url or os.getenv("OPENROUTER_BASE_URL")
        self.api_key = api_key or config.openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        
        if not self.base_url or not self.api_key:
            raise ValueError("Must provide base_url and api_key either directly, via config, or via environment variables")
            
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )
        
        # Build comprehensive bail instructions
        bail_instruction = """
        Important Instructions:
        1. You are a specialized assistant with a specific task. Stay focused on that task.
        2. Do not engage in conversation or ask follow-up questions.
        3. If you cannot complete the task with the information and tools provided, respond with BAIL.
        
        When to BAIL:
        - If required information is missing
        - If the request is unclear or ambiguous
        - If you're unsure about anything
        - If the task is outside your specific role
        
        How to BAIL:
        Respond with: BAIL: <clear explanation of why you cannot proceed>
        
        Remember: It's better to bail clearly than to guess wildly or ask for clarification.
        """
        
        self.system_prompt = instructions + "\n\n" + bail_instruction
        self.model = model or config.default_model
        self.max_iterations = max_iterations or config.max_iterations
        
        # Initialize json_response and response_format
        self.json_response = None
        self.response_format = None
        
        # Store the original Pydantic model class if provided
        self.pydantic_model = json_response if isinstance(json_response, type) and issubclass(json_response, BaseModel) else None
        
        if json_response:
            # Convert json_response schema or Pydantic model to OpenAI format
            if self.pydantic_model:
                self.json_response = json_response.model_json_schema()
            else:
                self.json_response = json_response

            # Only use response_format for OpenAI models
            if "openai" in self.model.lower():
                self.response_format = {"type": "json_object"}
            
            # Always include JSON instructions in system prompt
            self.system_prompt += (
                "\n\nYou MUST respond with valid JSON matching this schema:\n" 
                + json.dumps(self.json_response, indent=2)
                + "\nAlways respond with properly formatted JSON, never with plain text."
            )
        
        self.tools = tools
        self.tool_schemas = [t['schema'] for t in tools.values()] if tools else None
        self.tool_functions = {name: t['function'] for name, t in tools.items()} if tools else None
        
        self.temperature = temperature
        
        logger.debug("Pup initialized with model: {} and max_iterations: {}", 
                    self.model, self.max_iterations)

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
        tools: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Union[str, Dict[str, Any], BaseModel]:
        """
        Run a conversation with the given user message and optional tools.
        
        Args:
            user_message: The user's message to respond to
            tools: Optional dictionary of tool configurations to override instance tools
            
        Returns:
            The final response as either:
            - A string (if no json_response specified)
            - A dict (if json_response is a schema dict)
            - A Pydantic model instance (if json_response is a Pydantic model class)
        """
        try:
            # Use instance tools if not overridden by run arguments
            if tools:
                tool_schemas = [t['schema'] for t in tools.values()]
                tool_functions = {name: t['function'] for name, t in tools.items()}
            else:
                tool_schemas = self.tool_schemas
                tool_functions = self.tool_functions
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            logger.debug("Starting conversation with user message: {}", user_message)
            if tool_schemas:
                logger.debug("Available tools: {}", list(tool_functions.keys()))

            iterations = 0
            while iterations < self.max_iterations:
                iterations += 1
                logger.info(f"Starting iteration {iterations}/{self.max_iterations}")
                
                # Only include tools if they're provided
                completion_args = {
                    "model": self.model,
                    "messages": messages,
                }
                if tool_schemas:
                    completion_args["tools"] = tool_schemas
                if self.response_format:
                    completion_args["response_format"] = self.response_format
                if self.temperature is not None:
                    completion_args["temperature"] = self.temperature
                
                # Log the completion arguments
                logger.debug("Sending completion request with args: {}", 
                            {k: v for k, v in completion_args.items() if k != "messages"})
                
                completion = self.client.chat.completions.create(**completion_args)
                
                # Log the full completion response
                logger.debug("Raw completion response: {}", completion)
                
                response_message = completion.choices[0].message
                logger.debug("Response message content: {}", response_message.content)
                logger.debug("Response message tool calls: {}", response_message.tool_calls)

                # First, check if we have a valid response content
                if response_message.content and response_message.content.strip():
                    logger.info("Processing response content")
                    content = response_message.content.strip()
                    
                    # Check for bail message first
                    if content.startswith("BAIL:"):
                        raise PupError(
                            type=PupError.COGNITIVE,
                            subtype=PupError.UNCERTAIN,
                            message=content[5:].strip(),
                            details={"user_message": user_message}
                        )

                    # If JSON response is expected, parse and validate
                    if self.json_response:
                        try:
                            # Clean markdown code blocks if present
                            if content.startswith('```'):
                                content = content.split('```')[1]
                                if content.startswith('json'):
                                    content = content[4:]
                                content = content.strip()
                            
                            # Parse and validate JSON
                            cleaned_data = json.loads(content)
                            validate_json(instance=cleaned_data, schema=self.json_response)
                            
                            # Convert to Pydantic model if specified
                            if self.pydantic_model:
                                return self.pydantic_model(**cleaned_data)
                            return cleaned_data
                        except (json.JSONDecodeError, ValidationError) as e:
                            logger.error("Response validation failed: {}", e)
                            raise PupError(
                                type=PupError.TECHNICAL,
                                subtype=PupError.SCHEMA_VIOLATION,
                                message=str(e),
                                details={"content": content}
                            )
                    else:
                        return content

                # Only handle tool calls if tools were provided
                if tool_schemas and response_message.tool_calls:
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

        except PupError:
            # Re-raise PupErrors without modification
            raise
        except json.JSONDecodeError as e:
            raise PupError(
                type=PupError.TECHNICAL,
                subtype=PupError.INVALID_JSON,
                message="Failed to parse JSON response",
                details={"error": str(e)}
            ) from e
        except ValidationError as e:
            raise PupError(
                type=PupError.TECHNICAL,
                subtype=PupError.SCHEMA_VIOLATION,
                message="Response validation failed",
                details={"error": str(e)}
            ) from e
        except ValueError as e:
            raise PupError(
                type=PupError.TECHNICAL,
                subtype=PupError.MISSING_REQUIREMENTS,
                message=str(e)
            ) from e
        except Exception as e:
            if isinstance(e.__cause__, PupError):
                raise e.__cause__
            raise PupError(
                type=PupError.TECHNICAL,
                message="Unexpected error",
                details={"error": str(e)}
            ) from e 

    def as_tool(self, tool_name: Optional[str] = None, tool_description: Optional[str] = None) -> Type[BaseTool]:
        """
        Create a tool class from this pup.
        
        Args:
            tool_name: Override the tool name (defaults to pup's name)
            tool_description: Override the tool description (defaults to pup's description)
            
        Returns:
            A new BaseTool subclass that wraps this pup
        """
        pup = self  # Capture self reference for closure
        
        class PupTool(BaseTool):
            name = tool_name or pup.name or f"unnamed_pup_{id(pup)}"
            description = tool_description or pup.description or "No description provided"
            
            async def execute(self, prompt: str) -> str:
                """
                Run the pup with the given prompt
                
                Args:
                    prompt: The input prompt for the pup
                """
                result = await pup.run(prompt)
                
                # If result is a Pydantic model, convert to JSON
                if isinstance(result, BaseModel):
                    return result.model_dump_json(indent=4)
                # If result is a dict, convert to JSON string
                elif isinstance(result, dict):
                    return json.dumps(result, indent=4)
                # Otherwise return as string
                return str(result)
                
        return PupTool

    def register_as_tool(self, registry: ToolRegistry, tool_name: Optional[str] = None, tool_description: Optional[str] = None):
        """
        Register this pup as a tool in the given registry
        
        Args:
            registry: The ToolRegistry to register with
            tool_name: Override the tool name (defaults to pup's name)
            tool_description: Override the tool description (defaults to pup's description)
        """
        tool_class = self.as_tool(tool_name=tool_name, tool_description=tool_description)
        registry.register_tool(tool_class) 