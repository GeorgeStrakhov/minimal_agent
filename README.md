# SmartPups Framework

A lightweight, extensible framework for building AI pups that can use tools and maintain memory across conversations. Features strong typing, input validation, and automatic schema generation.

## Overview

This framework provides a simple way to create AI pups that can:
- Use multiple tools/functions with input validation
- Maintain memory across conversations
- Return structured JSON responses
- Handle multi-step conversations
- Process tool calls and responses in parallel with final responses

## Core Components

### Pup (`pup.py`)

The main pup class that handles:
- Async conversation management
- Tool calling and response processing
- JSON validation and cleaning
- Response handling

```python
pup = Pup(
    base_url="your_api_base_url",
    api_key="your_api_key",
    model="model_name",
    max_iterations=5
)

# Run a conversation
response = await pup.run(messages, tools, tool_functions)
```

### Tool System

Tools are self-contained modules that:
- Auto-generate their OpenAI function schemas
- Validate inputs using Pydantic
- Support async execution
- Provide clear error messages

Example tool implementation:

```python
from tools.base_tool import BaseTool
from tools.models import TemperatureUnit
from pydantic import BaseModel, Field

class WeatherRequest(BaseModel):
    location: str = Field(..., min_length=1, description="City name")
    unit: TemperatureUnit = Field(
        default=TemperatureUnit.CELSIUS,
        description="Temperature unit to use"
    )

class WeatherTool(BaseTool):
    name = "get_weather"
    description = "Get current weather for a location"
    
    async def execute(
        self,
        location: str,
        unit: TemperatureUnit = TemperatureUnit.CELSIUS
    ) -> str:
        """Get weather information for a location"""
        # Validate inputs
        request = WeatherRequest(location=location, unit=unit)
        # Implementation...
        return f"Weather in {location} is sunny"
```

### Memory System (`tools/memory/`)

A tool-based memory system that allows the pup to:
- Save information for future use
- Recall previously stored information
- Validate memory operations
- Persist data between conversations

```python
# Memory tools are automatically discovered and loaded
remember_tool = registry.tools["remember"]()
recall_tool = registry.tools["recall"]()

# Save data
await remember_tool.execute(key="user_preference", value="celsius")

# Recall data
result = await recall_tool.execute(key="user_preference")
```

## Usage

1. Set up your environment:
```bash
pip install -r requirements.txt
```
**I'd highly recommend using uv**

2. Create a `.env` file with your API credentials:
```env
OPENROUTER_BASE_URL=your_api_base_url
OPENROUTER_API_KEY=your_api_key
```

3. Create a new tool:
```python
# tools/custom/my_tool.py
from tools.base_tool import BaseTool
from pydantic import BaseModel, Field

class MyToolInput(BaseModel):
    param: str = Field(..., min_length=1, description="Parameter description")

class MyTool(BaseTool):
    name = "my_tool"
    description = "Tool description"
    
    async def execute(self, param: str) -> str:
        # Validate input
        request = MyToolInput(param=param)
        return f"Processed {request.param}"
```

4. Run a conversation:
```python
from tools.registry import ToolRegistry

# Tools are automatically discovered
registry = ToolRegistry()
registry.discover_tools()

# Get tool schemas and functions
tools = registry.get_schemas()
tool_functions = registry.get_tool_functions()

# Run conversation
response = await pup.run(messages, tools, tool_functions)
```

## Features

### Tool System
- Automatic schema generation from type hints and docstrings
- Input validation using Pydantic models
- Support for enums and complex types
- Coordinate parsing and validation
- Automatic tool discovery and registration

### Memory System
- Key-value storage with validation
- File-based persistence
- Error handling and validation
- Automatic schema generation

### Response Handling
- JSON schema validation
- Markdown cleaning
- Support for both structured and unstructured responses
- Error handling for malformed responses

## Best Practices

1. **Tool Development**
   - Use Pydantic models for input validation
   - Provide clear error messages
   - Use type hints and docstrings
   - Keep tools focused and single-purpose

2. **Input Validation**
   - Define constraints using Pydantic Field
   - Use enums for fixed choices
   - Validate early in the execute method
   - Return clear error messages

3. **Memory Usage**
   - Use consistent key naming
   - Validate both keys and values
   - Handle missing values gracefully
   - Clean up old entries when appropriate

4. **Error Handling**
   - Validate inputs before processing
   - Provide informative error messages
   - Handle edge cases explicitly
   - Log errors appropriately

## Limitations

- File-based memory system just for a test, not be suitable for anything real
- Tool calls are processed sequentially
- Memory is limited to simple key-value storage
- No built-in support for streaming responses

## License

MIT License - feel free to use this in your own projects!