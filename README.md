<p align="center">
  <img src="https://raw.githubusercontent.com/georgestrakhov/smartpup/main/docs/assets/smartpup.png" alt="SmartPup Logo" width="300"/>
</p>

# SmartPup

A minimalistic framework for building reliable AI agents (pups) that do exactly what you tell them to do, without extra magic.

## Why?

The existing agent frameworks feel too complex and bloated. Maybe they are right for some use cases, but my feeble brain needed something simpler. All this talk of "agents" is tricky because you can't really rely on an LLM to do what you want it to do. Not yet anyway. So I really want is not smart agents that will figure things out, but simply smart functions - that I can call with a system prompt and a bunch of tools and they will reliably do the one thing they are supposed to do. And if they can't - they will fail, ideally explaining why.

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
        system_prompt="You are a weather assistant. Check the weather and report it as a short poem.",
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

- **Weather**: Get current weather for any location
- **DateTime**: Get current date/time in various formats
- **Memory**: Simple key-value storage for persistence
- **Translate**: Text translation between languages

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
```

## Examples

Check the [examples](examples/) directory for more usage examples:
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

MIT License - see [LICENSE](LICENSE) for details.