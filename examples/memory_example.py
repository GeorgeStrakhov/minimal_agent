import asyncio
from smartpup import Pup, ToolRegistry

async def main():
    # Initialize and get memory tools
    registry = ToolRegistry()
    registry.discover_tools()
    
    # Create memory pup
    memory_pup = Pup(
        instructions="You are an system that can remembers things about the user. Use the remember tool to store information. Store using 'remember' tool with the relevant key (e.g. 'favorite_color') and value (e.g. 'black'). Respond with a confirmation. If the user asks for information, use the recall tool to retrieve it, providing the key (e.g. 'favorite_color') and the value will be returned.",
        tools=registry.get_tools(["remember", "recall"])
    )

    # Store one piece of information
    response = await memory_pup.run("Remember that my favorite color is blue.")
    print(f"Response: {response}")

    # This should store the information into the file specified in the config or by default memory.json

    # Retrieve the information
    response = await memory_pup.run("What is my favorite color? Use the recall tool to retrieve the information using relevant key, e.g. 'favorite_color'")
    print(f"Response: {response}")

if __name__ == "__main__":
    asyncio.run(main()) 