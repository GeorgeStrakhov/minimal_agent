from ..base_tool import BaseTool
from typing import Optional
import random

class GetWeatherTool(BaseTool):
    name = "get_current_weather"
    description = "Get current weather for a location"
    
    async def execute(
        self,
        location: str,
        coordinates: Optional[str] = None,
        unit: str = "celsius"
    ) -> str:
        """
        Get weather information for a location
        
        Args:
            location: The city or place name to get weather for
            coordinates: Optional latitude/longitude coordinates (e.g. "42.3601,-71.0589")
            unit: Temperature unit to use (celsius or fahrenheit)
            
        Returns:
            A string describing the current weather
        """
        # Mock implementation
        temp = random.randint(-5, 30)
        conditions = random.choice(["sunny", "partly cloudy", "overcast", "rainy"])
        
        if coordinates:
            location_str = f"at coordinates {coordinates}"
        else:
            location_str = f"in {location}"
            
        temp_str = f"{temp}°{'C' if unit == 'celsius' else 'F'}"
        
        return f"The weather {location_str} is {temp_str} and {conditions}" 