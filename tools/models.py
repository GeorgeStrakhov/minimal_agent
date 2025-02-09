from enum import Enum
from pydantic import BaseModel, Field

class TemperatureUnit(str, Enum):
    CELSIUS = "celsius"
    FAHRENHEIT = "fahrenheit"

class Coordinates(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude between -90 and 90")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude between -180 and 180")
    
    @classmethod
    def from_string(cls, coord_str: str) -> "Coordinates":
        """Convert a coordinate string (e.g. '42.3601,-71.0589') to a Coordinates object"""
        try:
            lat, lon = map(float, coord_str.split(','))
            return cls(latitude=lat, longitude=lon)
        except (ValueError, TypeError):
            raise ValueError(
                "Invalid coordinates format. Expected 'latitude,longitude' "
                "(e.g. '42.3601,-71.0589')"
            )
    
    def __str__(self) -> str:
        """Convert coordinates to string format"""
        return f"{self.latitude},{self.longitude}" 