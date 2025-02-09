from openai import OpenAI
import os
from typing import List, Dict, Any, Callable, Optional
import json
from loguru import logger

class Agent:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str = "google/gemini-2.0-flash-001"
    ):
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )
        self.model = model
        logger.debug("Agent initialized with model: {}", model)

    def run(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        tool_functions: Dict[str, Callable]
    ) -> str:
        """
        Run the conversation with the given messages and tools until a final response is reached.
        
        Args:
            messages: List of message dictionaries in OpenAI format
            tools: List of tool definitions in OpenAI format
            tool_functions: Dictionary mapping tool names to their actual functions
            
        Returns:
            The final response from the assistant
        """
        logger.debug("Starting conversation with {} messages", len(messages))
        logger.debug("Available tools: {}", list(tool_functions.keys()))

        while True:
            logger.info("Making API call to LLM")
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools
            )
            logger.debug("Received response: {}", completion)

            response_message = completion.choices[0].message

            # If there's no tool calls, we can return the response
            if not response_message.tool_calls:
                logger.info("No tool calls, returning final response")
                return response_message.content

            # Handle tool calls
            logger.info("Processing tool calls")
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                
                if function_name not in tool_functions:
                    logger.warning("Unknown tool call received: {}", function_name)
                    raise ValueError(f"Unknown tool: {function_name}")

                logger.debug("Handling function call: {}", tool_call)
                # Parse the arguments
                function_args = json.loads(tool_call.function.arguments)
                logger.debug("Function arguments: {}", function_args)
                
                # Call the function
                function = tool_functions[function_name]
                function_response = function(**function_args)
                logger.debug("Function response: {}", function_response)

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