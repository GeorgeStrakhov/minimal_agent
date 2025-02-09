# Minimal Agent Framework

A lightweight, extensible framework for building AI agents that can use tools and maintain memory across conversations.

## Overview

This framework provides a simple way to create AI agents that can:
- Use multiple tools/functions
- Maintain memory across conversations
- Return structured JSON responses
- Handle multi-step conversations
- Process tool calls and responses in parallel with final responses

## Core Components

### Agent (`agent.py`)

The main agent class that handles:
- Conversation management
- Tool calling and response processing
- JSON validation and cleaning
- Response handling

```python
agent = Agent(
    base_url="your_api_base_url",
    api_key="your_api_key",
    model="model_name",
    max_iterations=5
)
```

Key features:
- Can process multiple tool calls in a single conversation turn
- Supports JSON schema validation for responses
- Handles markdown and code block formatting in responses
- Maintains conversation context across iterations

### Memory System (`memory.py`)

A simple file-based memory system that allows the agent to:
- Save information for future use
- Recall previously stored information
- Persist data between conversations

```python
memory = FileMemory(file_path="memory.json")
memory.save("key", "value")
value = memory.get("key")
```

### Main Application (`main.py`)

Demonstrates how to:
- Set up the agent with tools and memory
- Define tool functions and their schemas
- Structure conversations with system prompts
- Handle JSON responses and validation

## Usage

1. Set up your environment:
```bash
pip install openai python-dotenv loguru jsonschema
```

2. Create a `.env` file with your API credentials:

We use OpenRouter to proxy the requests to the LLM, so that any model can be used (that supports tool calling).

```env
OPENROUTER_BASE_URL=your_api_base_url
OPENROUTER_API_KEY=your_api_key
```

3. Define your tools:
```python
def my_tool(param: str) -> str:
    return f"Processed {param}"

tools = [{
    "type": "function",
    "function": {
        "name": "my_tool",
        "description": "Tool description",
        "parameters": {
            "type": "object",
            "properties": {
                "param": {"type": "string"}
            },
            "required": ["param"]
        }
    }
}]

tool_functions = {
    "my_tool": my_tool
}
```

4. Create a conversation:
```python
messages = [
    {
        "role": "system",
        "content": "System instructions..."
    },
    {
        "role": "user",
        "content": "User message..."
    }
]

response = agent.run(messages, tools, tool_functions)
```

## Features

### Tool Calling
- Tools can be called multiple times in a single conversation
- Tool calls can be processed alongside final responses
- Tool responses are automatically added to conversation context

### Memory System
- For demo only, the memory is stored in a file called `memory.json`
- File-based persistence
- Simple key-value storage

### Response Handling
- JSON schema validation
- Markdown cleaning
- Support for both structured and unstructured responses
- Error handling for malformed responses

## Example

```python
# Initialize components
memory = FileMemory()
agent = Agent(base_url=os.getenv("API_BASE_URL"), api_key=os.getenv("API_KEY"))

# Define a tool
def get_weather(location: str) -> str:
    return f"Weather in {location} is sunny"

# Set up the conversation
messages = [
    {
        "role": "system",
        "content": "You are a weather assistant..."
    },
    {
        "role": "user",
        "content": "What's the weather in London?"
    }
]

# Run the conversation
response = agent.run(messages, tools, tool_functions)
print(response)
```

## Best Practices

1. Always provide clear system instructions
2. Define JSON schemas for structured responses
3. Include error handling for tool calls
4. Use memory for maintaining context
5. Keep tool functions simple and focused

## Limitations

- File-based memory system may not be suitable for high-concurrency applications
- Tool calls are processed sequentially
- Memory is limited to simple key-value storage
- No built-in support for streaming responses