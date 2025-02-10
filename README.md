# SmartPup Framework

A an opinionated, minimalistic framework for building AI pups (a.k.a. agents) who are reliable and do what you tell them to do, without extra magic.

* uses OpenRouter to support multiple LLM providers
* uses Pydantic for input and output validation
* treats the idea of "Agents" as simply smart functions: you tell them what to do and what kind of output you expect - and they run off and do it predictably, with the output you expect. Or they bail.
* our pups (agents) are not trying to hold conversation history etc. beyond the scope of their current task.

## Overview

This framework provides a simple way to create AI pups that can:
- Use tools with input validation
- Remember information across conversations (via a memory tool if needed)
- Return structured JSON responses
- Handle multi-step conversations
- Bail gracefully when uncertain

## Core Components

### Pup (`pup.py`)

A pup can be created with or without tools and with optional JSON response validation:

```python
from pydantic import BaseModel, Field
from tools.registry import ToolRegistry

# Define expected response structure using Pydantic
class WeatherResponse(BaseModel):
    location: str = Field(..., description="Name of the location")
    coordinates: dict = Field(..., description="Geographic coordinates")
    temperature: dict = Field(..., description="Temperature information")
    conditions: str = Field(..., description="Weather conditions description")

# Initialize tool registry and discover tools
registry = ToolRegistry()
registry.discover_tools()  # Discovers all tools
# Or load specific tools:
# registry.discover_tools(tool_names=["get_weather", "get_datetime"])

# Basic pup without tools
zen_pup = Pup(
    system_prompt="You are a zen master, you always respond with a koan and nothing else."
)

# Weather pup with specific tools
weather_tools = registry.get_tools(["get_weather", "remember"])
weather_pup = Pup(
    system_prompt="You are a weather assistant...",
    json_response=WeatherResponse,  # Pydantic model for validation
    tools=weather_tools            # Dictionary containing tool schemas and functions
)

# Run conversations
response = await zen_pup.run("What is the sound of one hand clapping?")
weather = await weather_pup.run("What's the weather in Chicago?")
```

### Tools

Tools are self-contained modules that give pups additional capabilities. They:
- Auto-generate their schemas from Python type hints
- Validate inputs using Pydantic
- Support async execution
- Are automatically discovered and managed by the ToolRegistry

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

### Tool Registry

The ToolRegistry manages tool discovery and instantiation:

```python
# Initialize registry
registry = ToolRegistry()

# Load all available tools
registry.discover_tools()

# Or load specific tools by name
registry.discover_tools(tool_names=["get_weather", "get_datetime"])

# Get tools for a specific pup
weather_tools = registry.get_tools(["get_weather", "remember"])
datetime_tools = registry.get_tools(["get_datetime"])

# Create pup with tools
weather_pup = Pup(
    system_prompt="You are a weather assistant...",
    tools=weather_tools
)
```

### Custom Tools

You can create custom tools in two ways:

#### 1. Quick Mock Tools (Great for Testing)

Define a tool directly in your code:

```python
from tools import BaseTool

class MockWeatherTool(BaseTool):
    name = "get_weather"
    description = "Get mock weather for a location"
    
    async def execute(
        self,
        location: str,
        unit: str = "celsius"
    ) -> str:
        """Get mock weather for a location"""
        return f"It's always sunny and 22°{unit[0].upper()} in {location}!"

# Register and use the mock tool
registry = ToolRegistry()
registry.register_tool(MockWeatherTool)
weather_tools = registry.get_tools(["get_weather"])
```

#### 2. Full Tool Implementation

Create a proper tool package in `tools/custom/`:

```bash
mkdir -p tools/custom/my_tool
touch tools/custom/my_tool/__init__.py
```

Then implement your tool:

```python
# tools/custom/my_tool/my_tool.py
from tools import BaseTool, EnvVar, ToolEnv
from pydantic import BaseModel, Field

class MyTool(BaseTool):
    name = "my_tool"
    description = "Description of what my tool does"
    
    # Optional: Define required environment variables
    env = ToolEnv(vars=[
        EnvVar(
            name="MY_API_KEY",
            description="API key for my service",
            required=True
        )
    ])
    
    async def execute(
        self,
        param1: str,
        param2: int = 42
    ) -> str:
        """
        Tool implementation
        
        Args:
            param1: Description of param1
            param2: Description of param2
        """
        return f"Tool response: {param1}, {param2}"
```

Export it in `__init__.py`:

```python
# tools/custom/my_tool/__init__.py
from .my_tool import MyTool

__all__ = ['MyTool']
```

The tool will be auto-discovered when you call `registry.discover_tools()`.

### Memory System

A simple key-value store that persists between conversations:

```python
# Get memory tools
memory_tools = registry.get_tools(["remember", "recall"])

# Create pup with memory capabilities
memory_pup = Pup(
    system_prompt="You are an assistant that remembers things...",
    tools=memory_tools
)

# Use memory in conversations
await memory_pup.run("Remember that my favorite color is blue")
await memory_pup.run("What's my favorite color?")
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

# Load tools if needed
registry = ToolRegistry()
registry.discover_tools()
tools = registry.get_tools()  # Get all tools
# Or get specific tools:
# tools = registry.get_tools(["get_weather", "get_datetime"])

# Create a pup
pup = Pup(
    system_prompt="You are a helpful assistant...",
    tools=tools  # Optional
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
   - Use Pydantic models for response validation

2. **Tool Management**
   - Use ToolRegistry to manage tools
   - Load only the tools each pup needs
   - Group related tools when appropriate
   - Keep tool implementations focused and testable

3. **Handle Errors**
   - Validate inputs early
   - Provide clear error messages
   - Log important information
   - Let pups bail when uncertain

4. **Model Compatibility**
   - Works with OpenAI, Google, Anthropic models via OpenRouter
   - Automatically adapts JSON handling for different providers
   - Use appropriate model for the task

## Limitations

- Simple file-based memory system (not for production)
- Sequential tool execution
- No streaming support

## License

MIT License - feel free to use this in your own projects!