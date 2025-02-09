from ..base_tool import BaseTool
from ..models import TemperatureUnit, Coordinates
from typing import Optional
import random
from pydantic import BaseModel, Field

class WeatherRequest(BaseModel):
    location: str = Field(..., min_length=1, description="The city or place name to get weather for")
    coordinates: Optional[str] = Field(
        None, 
        pattern=r'^-?\d+\.?\d*,-?\d+\.?\d*$',
        description="Optional latitude/longitude coordinates (e.g. '42.3601,-71.0589')"
    )
    unit: TemperatureUnit = Field(
        default=TemperatureUnit.CELSIUS,
        description="Temperature unit to use"
    )

class GetWeatherTool(BaseTool):
    name = "get_current_weather"
    description = "Get current weather for a location"
    
    async def execute(
        self,
        location: str,
        coordinates: Optional[str] = None,
        unit: TemperatureUnit = TemperatureUnit.CELSIUS
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
        # Validate inputs
        request = WeatherRequest(
            location=location,
            coordinates=coordinates,
            unit=unit
        )
        
        # Parse coordinates if provided
        coords = None
        if request.coordinates:
            try:
                coords = Coordinates.from_string(request.coordinates)
            except ValueError as e:
                return str(e)
        
        # Mock implementation
        temp = random.randint(-5, 30)
        conditions = random.choice(["sunny", "partly cloudy", "overcast", "rainy"])
        
        if coords:
            location_str = f"at coordinates {coords}"
        else:
            location_str = f"in {location}"
            
        temp_str = f"{temp}°{'C' if unit == TemperatureUnit.CELSIUS else 'F'}"
        
        return f"The weather {location_str} is {temp_str} and {conditions}" 