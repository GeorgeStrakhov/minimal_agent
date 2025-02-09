from ..base_tool import BaseTool
from ..models import TemperatureUnit, Coordinates
from typing import Optional
import httpx
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
        
        try:
            async with httpx.AsyncClient() as client:
                # If coordinates aren't provided, get them from the location name
                if not request.coordinates:
                    # Use OpenStreetMap Nominatim API to get coordinates
                    geocode_url = f"https://nominatim.openstreetmap.org/search"
                    params = {
                        "q": request.location,
                        "format": "json",
                        "limit": 1
                    }
                    headers = {
                        "User-Agent": "MinimalAgentFramework/1.0"  # Required by Nominatim
                    }
                    
                    response = await client.get(geocode_url, params=params, headers=headers)
                    response.raise_for_status()
                    
                    locations = response.json()
                    if not locations:
                        return f"Could not find coordinates for location: {request.location}"
                    
                    lat = float(locations[0]["lat"])
                    lon = float(locations[0]["lon"])
                    coords = Coordinates(latitude=lat, longitude=lon)
                else:
                    try:
                        coords = Coordinates.from_string(request.coordinates)
                    except ValueError as e:
                        return str(e)
                
                # Get weather from OpenMeteo API
                weather_url = "https://api.open-meteo.com/v1/forecast"
                params = {
                    "latitude": coords.latitude,
                    "longitude": coords.longitude,
                    "current": ["temperature_2m", "weather_code"],
                    "temperature_unit": "celsius" if unit == TemperatureUnit.CELSIUS else "fahrenheit"
                }
                
                response = await client.get(weather_url, params=params)
                response.raise_for_status()
                
                weather_data = response.json()
                
                # Map WMO weather codes to descriptions
                # https://open-meteo.com/en/docs
                weather_codes = {
                    0: "clear sky",
                    1: "mainly clear",
                    2: "partly cloudy",
                    3: "overcast",
                    45: "foggy",
                    48: "depositing rime fog",
                    51: "light drizzle",
                    53: "moderate drizzle",
                    55: "dense drizzle",
                    61: "slight rain",
                    63: "moderate rain",
                    65: "heavy rain",
                    71: "slight snow",
                    73: "moderate snow",
                    75: "heavy snow",
                    77: "snow grains",
                    80: "slight rain showers",
                    81: "moderate rain showers",
                    82: "violent rain showers",
                    85: "slight snow showers",
                    86: "heavy snow showers",
                    95: "thunderstorm",
                    96: "thunderstorm with slight hail",
                    99: "thunderstorm with heavy hail",
                }
                
                temp = weather_data["current"]["temperature_2m"]
                weather_code = weather_data["current"]["weather_code"]
                conditions = weather_codes.get(weather_code, "unknown conditions")
                
                location_str = f"at coordinates {coords}" if request.coordinates else f"in {request.location}"
                temp_str = f"{temp}°{'C' if unit == TemperatureUnit.CELSIUS else 'F'}"
                
                return f"The weather {location_str} is {temp_str} with {conditions}"
                
        except httpx.RequestError as e:
            return f"Error fetching weather data: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}" 