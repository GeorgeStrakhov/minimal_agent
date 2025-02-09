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
        # Find JSON content between triple backticks if present
        if '```' in content:
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
        
        # Remove any non-JSON text before or after the JSON object
        content = content.strip()
        first_brace = content.find('{')
        last_brace = content.rfind('}')
        if first_brace != -1 and last_brace != -1:
            content = content[first_brace:last_brace + 1]
        
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
        
        The agent can now provide a final response while also making tool calls.
        Tool calls will be processed before returning the final response.
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
            logger.debug("Model response: {}", response_message)

            # First, check if we have a valid response content
            final_response = None
            if response_message.content and response_message.content.strip():
                logger.info("Processing response content")
                
                if json_response:
                    try:
                        cleaned_content = self._clean_json_response(response_message.content)
                        logger.debug("Cleaned content for JSON parsing: {}", cleaned_content)
                        
                        response_content = json.loads(cleaned_content)
                        validate_json(instance=response_content, schema=json_response)
                        final_response = response_content
                    except (json.JSONDecodeError, ValidationError) as e:
                        logger.error("Response validation failed: {}", e)
                        if not response_message.tool_calls:
                            raise
                else:
                    final_response = response_message.content

            # Then, handle any tool calls
            if response_message.tool_calls:
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
                            "content": response_message.content,
                            "tool_calls": [tool_call]
                        },
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": function_response
                        }
                    ])
                    logger.debug("Updated messages: {}", messages)
                
                # Continue the conversation if we have tool calls
                continue

            # If we reach here, we have no more tool calls
            if final_response is None:
                logger.error("No valid response or tool calls received")
                raise ValueError("Model must provide either a valid response or tool calls")
                
            return final_response

        raise ValueError(f"Max iterations ({self.max_iterations}) reached without final response") 