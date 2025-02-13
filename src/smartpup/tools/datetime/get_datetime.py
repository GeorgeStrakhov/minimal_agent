from smartpup.tools.base import BaseTool
from datetime import datetime
from enum import Enum
from typing import Optional

class DateTimeFormat(str, Enum):
    FULL = "full"  # e.g. "Monday, January 1, 2024 15:30:45"
    DATE = "date"  # e.g. "2024-01-01"
    TIME = "time"  # e.g. "15:30:45"
    SIMPLE = "simple"  # e.g. "Jan 1, 2024 3:30 PM"

class GetDateTimeTool(BaseTool):
    name = "get_datetime"
    description = "Get the current date and time"
    
    async def execute(
        self,
        format: DateTimeFormat = DateTimeFormat.FULL,
        timezone: Optional[str] = None
    ) -> str:
        """
        Get the current date and time
        
        Args:
            format: The format to return the date/time in (full, date, time, or simple)
            timezone: Optional timezone name (e.g. 'America/New_York', 'UTC'). Defaults to system local time
            
        Returns:
            The current date and time in the requested format
        """
        try:
            if timezone:
                from zoneinfo import ZoneInfo
                current = datetime.now(ZoneInfo(timezone))
            else:
                current = datetime.now()

            if format == DateTimeFormat.FULL:
                return current.strftime("%A, %B %d, %Y %H:%M:%S")
            elif format == DateTimeFormat.DATE:
                return current.strftime("%Y-%m-%d")
            elif format == DateTimeFormat.TIME:
                return current.strftime("%H:%M:%S")
            else:  # SIMPLE
                return current.strftime("%b %d, %Y %I:%M %p")
                
        except Exception as e:
            return f"Error getting date/time: {str(e)}" 