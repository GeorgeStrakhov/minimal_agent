from tools.registry import ToolRegistry
from pup import Pup
import asyncio
from loguru import logger
import json
from errors import PupError
from pydantic import BaseModel, Field
from typing import Optional

class WeatherResponse(BaseModel):
    location: str = Field(..., description="Name of the location")
    coordinates: dict = Field(..., description="Geographic coordinates", example={
        "latitude": 48.8566,
        "longitude": 2.3522
    })
    temperature: dict = Field(..., description="Temperature information", example={
        "value": 22.5,
        "unit": "celsius"
    })
    conditions: str = Field(..., description="Weather conditions description")

async def main():
    # Initialize tool registry
    registry = ToolRegistry()
    
    # Load all tools
    registry.discover_tools()
    
    # Get translation tools
    translate_tools = registry.get_tools(["translate"])
    
    # Create translator pup
    translator_pup = Pup(
        system_prompt="""You are a translation assistant. Use the translate tool to translate text accurately.""",
        tools=translate_tools
    )

    try:
        # Test translations
        response = await translator_pup.run(
            "Translate 'Hello, how are you?' to Spanish"
        )
        print("\nTranslation:", response)
        
        response = await translator_pup.run(
            "Now translate 'I love programming' to French"
        )
        print("\nTranslation:", response)
        
    except PupError as e:
        if e.type == PupError.COGNITIVE:
            logger.error("Pup was confused: {} ({})", e.message, e.subtype)
        elif e.subtype == PupError.INVALID_JSON:
            logger.error("Pup didn't return valid JSON: {}", e.message)
        elif e.subtype == PupError.SCHEMA_VIOLATION:
            logger.error("Pup's JSON didn't match schema: {}", e.message)
        else:
            logger.error("Technical error: {} ({})", e.message, e.subtype)
            
        if e.details:
            logger.debug("Error details: {}", e.details)
    except Exception as e:
        logger.error("Unexpected error: {}", str(e))

if __name__ == "__main__":
    logger.info("Starting translation test")
    asyncio.run(main())