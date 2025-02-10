# SmartPup Framework

A an opinionated, minimalistic framework for building AI pups (a.k.a. agents) who are reliable and do what you tell them to do, without extra magic.

* uses OpenRouter and only works with models that support function calling
* uses Pydantic for input and output validation
* treats the idea of "Agents" as simply smart functions: you tell them what to do and what kind of output you expect - and they run off and do it predictably, with the output you expect. Or they bail.
* our pups (agents) are not trying to hold conversation history etc. beyond the scope of their current task.

## Overview

This framework provides a simple way to create AI pups that can:
- Use tools with input validation
- Remember information across conversations (via a memory tool if needed)
- Return structured JSON responses
- Handle multi-step conversations

## Core Components

### Pup (`pup.py`)

A pup can be created with or without tools:

```python
# Basic pup without tools
zen_pup = Pup(
    system_prompt="You are a zen master, you always respond with a koan and nothing else."
)

# Advanced pup with tools and JSON validation
weather_pup = Pup(
    system_prompt="You are a weather assistant...",
    json_response=json_schema,  # Optional schema for validation
    tools=tools,               # Optional tools for capabilities
    tool_functions=tool_functions
)

# Run conversations
response = await zen_pup.run("What is the sound of one hand clapping?")
response = await weather_pup.run("What's the weather in Chicago?")
```

### Tools

Tools are self-contained modules that give pups additional capabilities. They:
- Auto-generate their schemas from Python type hints
- Validate inputs using Pydantic
- Support async execution

Example tool:

```python
from tools.base_tool import BaseTool
from pydantic import BaseModel, Field

class WeatherRequest(BaseModel):
    location: str = Field(..., description="City name")
    unit: str = Field(default="celsius", description="Temperature unit")

class WeatherTool(BaseTool):
    name = "get_weather"
    description = "Get current weather for a location"
    
    async def execute(self, location: str, unit: str = "celsius") -> str:
        request = WeatherRequest(location=location, unit=unit)
        # Implementation...
        return f"Weather in {location} is sunny"
```

### Memory System

A simple key-value store that persists between conversations:

```python
# Save data
await remember_tool.execute(key="last_city", value="Chicago")

# Recall data
result = await recall_tool.execute(key="last_city")
```

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt  # Using uv is recommended
```

2. Set up your API credentials in `.env`:
```env
OPENROUTER_BASE_URL=your_api_base_url
OPENROUTER_API_KEY=your_api_key
```

3. Create a pup and run a conversation:
```python
from tools.registry import ToolRegistry
from pup import Pup

# Optional: Load tools if needed
registry = ToolRegistry()
registry.discover_tools()
tools = registry.get_schemas()
tool_functions = registry.get_tool_functions()

# Create a pup
pup = Pup(
    system_prompt="You are a helpful assistant...",
    tools=tools,               # Optional
    tool_functions=tool_functions  # Optional
)

# Run a conversation
response = await pup.run("Hello! Can you help me?")
print(response)
```

## Best Practices

1. **Keep It Simple**
   - One tool = one clear purpose
   - Clear system prompts
   - Explicit validation rules

2. **Handle Errors**
   - Validate inputs early
   - Provide clear error messages
   - Log important information

## Limitations

- Simple file-based memory system (not for production)
- Sequential tool execution
- No streaming support

## License

MIT License - feel free to use this in your own projects!