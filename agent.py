from openai import OpenAI
import os
from typing import List, Dict, Any, Callable, Optional, Union
import json
from loguru import logger
from jsonschema import validate as validate_json
from jsonschema.exceptions import ValidationError

class Agent:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str = "google/gemini-2.0-flash-001",
        max_iterations: int = 10
    ):
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )
        self.model = model
        self.max_iterations = max_iterations
        logger.debug("Agent initialized with model: {} and max_iterations: {}", 
                    model, max_iterations)

    def _clean_json_response(self, content: str) -> str:
        """
        Clean up the response content by removing markdown formatting and other non-JSON elements.
        """
        # Remove markdown code block formatting if present
        if content.startswith('```') and content.endswith('```'):
            # Remove first line if it contains ```json or similar
            lines = content.split('\n')
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines[-1].startswith('```'):
                lines = lines[:-1]
            content = '\n'.join(lines)
        
        # Remove any leading/trailing whitespace
        content = content.strip()
        
        return content

    def run(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        tool_functions: Dict[str, Callable],
        json_response: Optional[Dict[str, Any]] = None
    ) -> Union[str, Dict[str, Any]]:
        """
        Run the conversation with the given messages and tools until a final response is reached.
        
        Args:
            messages: List of message dictionaries in OpenAI format
            tools: List of tool definitions in OpenAI format
            tool_functions: Dictionary mapping tool names to their actual functions
            json_response: Optional JSON schema for validating the response
            
        Returns:
            Either a string response or a JSON object if json_response schema is provided
            
        Raises:
            ValueError: If max iterations reached or unknown tool called
            ValidationError: If JSON response doesn't match the provided schema
        """
        logger.debug("Starting conversation with {} messages", len(messages))
        logger.debug("Available tools: {}", list(tool_functions.keys()))

        if json_response:
            # Instead of adding a new system message, modify the existing one
            if messages and messages[0]["role"] == "system":
                current_content = messages[0]["content"]
                messages[0]["content"] = current_content + "\n\nYour final response must be a valid JSON object with this exact structure:\n" + json.dumps(json_response, indent=2)
            else:
                # If no system message exists, add one
                messages = [{
                    "role": "system",
                    "content": "You must respond with a valid JSON object in this format:\n" + json.dumps(json_response, indent=2)
                }] + messages

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
            logger.debug("Model response: {}", response_message)  # Add this for debugging

            # If there's no tool calls, we can process the final response
            if not response_message.tool_calls:
                logger.warning("Model generated response without using tools: {}", response_message.content)
                if iterations == 1:
                    logger.error("Model attempted to respond without using required tools!")
                    raise ValueError("Model must use tools before generating final response")
                
                logger.info("Processing final response after {} iterations", iterations)
                
                if json_response:
                    try:
                        # Clean up the response before parsing
                        cleaned_content = self._clean_json_response(response_message.content)
                        logger.debug("Cleaned content for JSON parsing: {}", cleaned_content)
                        
                        # Try to parse the response as JSON
                        response_content = json.loads(cleaned_content)
                        # Validate against the schema
                        validate_json(instance=response_content, schema=json_response)
                        return response_content
                    except json.JSONDecodeError as e:
                        logger.error("Failed to parse response as JSON: {}", e)
                        raise ValueError(f"Response is not valid JSON: {e}")
                    except ValidationError as e:
                        logger.error("JSON validation failed: {}", e)
                        raise
                
                return response_message.content

            # Handle tool calls
            logger.info("Processing tool calls")
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                
                if function_name not in tool_functions:
                    logger.warning("Unknown tool call received: {}", function_name)
                    raise ValueError(f"Unknown tool: {function_name}")

                logger.debug("Handling function call: {}", tool_call)
                function_args = json.loads(tool_call.function.arguments)
                logger.debug("Function arguments: {}", function_args)
                
                function = tool_functions[function_name]
                function_response = function(**function_args)
                logger.debug("Function response: {}", function_response)

                messages.extend([
                    {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tool_call]
                    },
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": function_response
                    }
                ])
                logger.debug("Updated messages: {}", messages)

        raise ValueError(f"Max iterations ({self.max_iterations}) reached without final response") 