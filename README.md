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

async def main():
    # Initialize tools
    registry = ToolRegistry()
    registry.discover_tools()
    
    # Create a weather pup
    weather_pup = Pup(
        instructions="You are a weather assistant. Check the weather and report it as a short poem.",
        tools=registry.get_tools(["get_current_weather"])
    )

    # Get weather
    response = await weather_pup.run("What's the weather in Amsterdam?")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
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

# Register and use the tool
registry = ToolRegistry()
registry.register_tool(CalculatorTool)


# Now you can use this tool in a pup
pup = Pup(
    instructions="You are a calculator. Use the calculator tool to perform calculations and return back the result, spelled out in letters.",
    tools=registry.get_tools(["calculator"])
)

response = await pup.run("What is 15 plus 10?")
print(response)

```

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

## Philosophy

SmartPup is built on these principles:
1. **One Task at a Time**: Each pup does one specific thing
2. **No Magic**: Clear, predictable behavior without hidden complexity
3. **Tool-First**: Tools provide clear interfaces for agent capabilities
4. **Independent Requests**: No conversation history or context bleeding

## License

MIT License - see [LICENSE](https://github.com/georgestrakhov/smartpup/blob/main/LICENSE) for details.