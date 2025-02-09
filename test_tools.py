import asyncio
from tools.registry import ToolRegistry
from loguru import logger

async def main():
    # Initialize registry
    registry = ToolRegistry()
    
    logger.info("Starting tool discovery...")
    registry.discover_tools()
    
    # Print discovered tools and their schemas
    logger.info("Discovered tools:")
    for name, tool_class in registry.tools.items():
        logger.info(f"\nTool: {name}")
        tool = tool_class()
        logger.info(f"Description: {tool.description}")
        logger.info(f"Schema: {tool.get_schema()}")
    
    if not registry.tools:
        logger.error("No tools were discovered!")
        return
        
    # Test memory tools
    if "remember" in registry.tools:
        remember = registry.tools["remember"]()
        # Test remembering
        result = await remember.execute(key="test_key", value="test_value")
        logger.info(f"\nRemember result: {result}")
    else:
        logger.error("Remember tool not found!")
    
    if "recall" in registry.tools:
        recall = registry.tools["recall"]()
        # Test recalling
        result = await recall.execute(key="test_key")
        logger.info(f"\nRecall result: {result}")
    else:
        logger.error("Recall tool not found!")
    
    if "get_current_weather" in registry.tools:
        # Test weather tool
        weather = registry.tools["get_current_weather"]()
        result = await weather.execute(
            location="London",
            unit="celsius"
        )
        logger.info(f"\nWeather result: {result}")
    else:
        logger.error("Weather tool not found!")

if __name__ == "__main__":
    asyncio.run(main()) 