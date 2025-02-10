from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Coordinates(BaseModel):
    latitude: float
    longitude: float

class Temperature(BaseModel):
    value: float
    unit: str = Field(default="celsius", pattern="^(celsius|fahrenheit)$")

class WeatherResponse(BaseModel):
    location: str
    coordinates: Coordinates
    temperature: Temperature
    conditions: str

class DateTimeInfo(BaseModel):
    full: str
    date: str
    time: str
    timestamp: Optional[str] = None

class TimeResponse(BaseModel):
    query: str
    timezone: str
    datetime: DateTimeInfo 