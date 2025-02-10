import asyncio
from smartpup import Pup, ToolRegistry

async def main():
    # Initialize and get translation tool
    registry = ToolRegistry()
    registry.discover_tools()
    
    # Create translator pup
    translator = Pup(
        system_prompt="You are a translator. Translate the given text to the requested language.",
        tools=registry.get_tools(["translate"])
    )

    # Translate one phrase
    response = await translator.run("Translate 'Hello, how are you?' to Spanish")
    print(f"Translation: {response}")

if __name__ == "__main__":
    asyncio.run(main()) 