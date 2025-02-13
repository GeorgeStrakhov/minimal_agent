<p align="center">
  <img src="https://raw.githubusercontent.com/georgestrakhov/smartpup/main/docs/assets/smartpup.png" alt="SmartPup Logo" width="300"/>
</p>

# SmartPup

A minimalistic "anti-agentic" framework for building reliable AI puppies that do exactly what you tell them to do, without extra magic. Give them some instructions, a response schema and a bunch of tools - and they will run off and do it. Or at least they will try and will bail clearly if they can't.

## Why?

The existing agent frameworks feel too complex and bloated. Maybe they are right for some use cases, but my feeble brain needed something simpler. All this talk of "agents" is tricky because you can't rely on an LLM to do what you want it to do. Not yet anyway. So what I want is not super-smart "agents" that will figure things out completely by themselves (spoiler: they won't). What I want is smart functions: you call them, you give some inputs, you know what you get back. And behind the scenes they may be doing some fuzzy stuff that a normal function won't be able to do. But on the outside - it's all solid and predictable. So I want smart functions, that you give them an instruction, a response schema and a bunch of tools and they will reliably do the one thing they are supposed to do. And if they can't - they will fail properly, ideally explaining why.

So less like superintelligent "agents" and more like well trained puppies. You tell them what to do and they do it, bringing back exactly what you needed in the form you needed. Maybe in the future there is some pavlovian conditioning and training. But for now they are just like your average well trained dog: excitable, reliable, and not very smart.

## Features

* Simple, predictable agents that do run off and do one thing at a time and if they can't - they don't invent shit. They fail clearly and explain why.
* Uses OpenRouter to support multiple LLM providers (OpenAI, Anthropic, Google, etc.)
* Built-in tool system with auto-discovery
* No conversation history - each request is independent
* Optional memory system for persistence when needed (built as a tool)
* Uses Pydantic for type safety

## Installation

```bash
pip install smartpup
```

## Quick Start

```python
import asyncio
from smartpup import Pup, ToolRegistry
from pydantic import BaseModel

# Define the expected response format
class WeatherReport(BaseModel):
    temperature: float
    conditions: str
    summary: str
    location: str

async def main():
    # Initialize and get weather tool
    registry = ToolRegistry()
    registry.discover_tools()
    
    # Create weather pup that uses the built-in weather tool
    weather_pup = Pup(
        instructions="You are a weather assistant. Check the weather and provide a structured report.",
        tools=registry.get_tools(["get_current_weather"]),
        json_response=WeatherReport
    )

    # Get weather
    response = await weather_pup.run("What's the weather in Amsterdam?")
    print(f"\nWeather in {response.location}:")
    print(f"Temperature: {response.temperature}°C")
    print(f"Conditions: {response.conditions}")
    print(f"Summary: {response.summary}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Response Schemas

SmartPup supports three types of responses:

1. **Plain Text**: Default behavior when no schema is specified
2. **Pydantic Models**: The recommended way to enforce typed responses

### Using Pydantic Models (Recommended)

```python
from pydantic import BaseModel
from typing import List, Optional

# Define your response model
class WeatherForecast(BaseModel):
    current_temp: float
    feels_like: float
    conditions: str
    hourly_forecast: List[str]
    warnings: Optional[List[str]] = None

# Create pup with typed response
weather_pup = Pup(
    instructions="You are a detailed weather forecaster...",
    tools=registry.get_tools(["get_current_weather"]),
    json_response=WeatherForecast  # Pup will return WeatherForecast instances
)

# Get typed response
forecast = await weather_pup.run("What's the weather forecast for Tokyo?")
print(f"Temperature: {forecast.current_temp}°C")
print(f"Feels like: {forecast.feels_like}°C")
print(f"Conditions: {forecast.conditions}")

# Access list fields
for hour in forecast.hourly_forecast:
    print(f"- {hour}")

# Safe access to optional fields
if forecast.warnings:
    for warning in forecast.warnings:
        print(f"Warning: {warning}")
```

Benefits of using Pydantic models:
- Type safety and validation
- IDE autocompletion support
- Clear response structure documentation
- Automatic conversion of JSON to Python objects
- Optional fields with default values
- Nested models and complex types

### Error Handling with Schemas

When using response schemas, SmartPup will raise a `PupError` if:
- The response doesn't match the schema (`PupError.SCHEMA_VIOLATION`)
- The JSON is malformed (`PupError.INVALID_JSON`)

```python
try:
    response = await weather_pup.run("What's the weather in Paris?")
    print(f"Temperature: {response.temperature}°C")
except PupError as e:
    if e.subtype == PupError.SCHEMA_VIOLATION:
        print(f"Response didn't match expected format: {e.message}")
    elif e.subtype == PupError.INVALID_JSON:
        print(f"Couldn't parse response as JSON: {e.message}")
```

## Environment Setup

Create a `.env` file:
```env
OPENROUTER_API_KEY=your-api-key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

## Built-in Tools

- **get_current_weather**: Get current weather for any location
- **get_datetime**: Get current date/time in various formats
- **memory**: Simple key-value storage for persistence
- **translate**: Text translation between languages

You can list all available tools and their parameters programmatically:

```python
from smartpup import ToolRegistry

# Initialize registry and discover tools
registry = ToolRegistry()
registry.discover_tools()

# Get list of all available tools with their descriptions and parameters
tools = registry.list_tools()
for tool in tools:
    print(f"\n{tool['name']}: {tool['description']}")
    print("Parameters:")
    for param_name, param_info in tool['parameters'].items():
        default = f" (default: {param_info['default']})" if param_info['default'] != 'None' else ''
        print(f"  - {param_name}: {param_info['type']}{default}")
```

## Creating Custom Tools

SmartPup supports two ways of creating tools:

1. **Regular Tools**: For well-defined operations with specific parameters
2. **Pup as Tool**: For more flexible, natural language interactions and hierarchical multi-agent interactions

### Method 1: Regular Tool Implementation

```python
from smartpup import BaseTool

class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Perform basic arithmetic operations"
    
    async def execute(
        self,
        operation: str,
        a: float,
        b: float
    ) -> str:
        """
        Perform basic arithmetic
        
        Args:
            operation: One of 'add', 'subtract', 'multiply', 'divide'
            a: First number
            b: Second number
        """
        if operation == "add":
            return f"Result: {a + b}"
        # ... other operations ...

# Register the tool
registry = ToolRegistry()
registry.register_tool(CalculatorTool)

# Now you can give it to a pup like you would normally do
math_solver = Pup(
    instructions="You are a math tutor. Use the calculator tool to solve problems.",
    tools=registry.get_tools(["calculator"])
)
```

### Method 2: Pup as Tool

```python
from smartpup import Pup

# Create a pup that can be used as a tool
text_calculator = Pup(
    name="text_calculator", # pay attention to the name - this is the name that will be used to call the tool. avoid name crashes. recommended to use namespacing / prefixing. e.g. "myproj_text_calculator"
    description="Convert text math problems into calculations",
    instructions="You are a math assistant that converts text problems into calculator operations."
)

# Register the pup as a tool
registry = ToolRegistry()
text_calculator.register_as_tool(registry)

# Use both tools in another pup
math_solver = Pup(
    instructions="You are a math tutor. Use the text_calculator tool to show the user how to perform calculations.",
    tools=registry.get_tools(["text_calculator"])
)
```

### When to Use Each Method

- Use **Regular Tools** when:
  - The operation has well-defined inputs and outputs
  - You need strict parameter validation
  - Performance is critical
  - The operation involves external APIs or systems

- Use **Pup as Tool** when:
  - When you are building a hierarchical multi-agent system
  - You need natural language understanding
  - The operation is more flexible or fuzzy
  - The tool needs to handle varied input formats
  - You want to chain capabilities

## Error types and error handling

SmartPup uses a structured error system through the `PupError` class. There are two main error types:

1. **Technical Errors** (`PupError.TECHNICAL`): System or API-level issues
   - `INVALID_JSON`: Failed to parse JSON response
   - `SCHEMA_VIOLATION`: Response didn't match expected schema
   - `MISSING_REQUIREMENTS`: Missing required tools or configuration

2. **Cognitive Errors** (`PupError.COGNITIVE`): LLM understanding or capability issues
   - `UNCERTAIN`: The pup is unsure and chooses to bail

### Example Error Handling

```python
from smartpup import Pup, PupError

async def main():
    weather_pup = Pup(
        instructions="You are a weather assistant...",
        tools=registry.get_tools(["get_current_weather"])
    )

    try:
        response = await weather_pup.run("What's the weather in Amsterdam?")
        print(response)
    except PupError as e:
        if e.type == PupError.COGNITIVE:
            print(f"Pup was uncertain: {e.message}")
        elif e.type == PupError.TECHNICAL:
            print(f"Technical error ({e.subtype}): {e.message}")
            if e.details:  # Additional error context
                print(f"Details: {e.details}")
        else:
            print(f"Unknown error: {e}")
```

### BAIL Responses

Pups are designed to fail gracefully using the BAIL mechanism when they:
- Cannot complete a task with available information
- Receive unclear or ambiguous requests
- Are unsure about any aspect of the task
- Are asked to perform tasks outside their role

When a pup bails, it raises a `PupError` with type `COGNITIVE` and subtype `UNCERTAIN`, including a clear explanation message.

### Error Details

All `PupError` instances include:
- `type`: Main error category (`TECHNICAL` or `COGNITIVE`)
- `subtype`: Specific error type (e.g., `INVALID_JSON`, `UNCERTAIN`)
- `message`: Human-readable error description
- `details`: Optional dictionary with additional context


## Usage Examples

Check the [examples](https://github.com/georgestrakhov/smartpup/tree/main/examples) directory for more usage examples:
- Basic weather reporting
- Translation service
- Memory usage
- Custom calculator tool

## Configuration

Optional global configuration:

```python
from smartpup import configure

configure(
    default_model="openai/gpt-4o-mini",  # Default LLM to use
    max_iterations=10,                    # Max tool call iterations
    memory_file="memory.json"            # For memory tools. alternatively you can set the environment variable MEMORY_FILE
)
```

## Development

For development:

```bash
git clone https://github.com/georgestrakhov/smartpup.git
cd smartpup
pip install -e ".[dev]"
pytest  # Run tests
```

## License

MIT License - see [LICENSE](https://github.com/georgestrakhov/smartpup/blob/main/LICENSE) for details.
