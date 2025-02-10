from typing import Optional
from dataclasses import dataclass
from loguru import logger

@dataclass
class EnvVar:
    """Represents a required environment variable"""
    name: str
    description: str
    required: bool = True

@dataclass 
class ToolEnv:
    """Collection of environment variables needed by a tool"""
    vars: list[EnvVar]
    
    def validate(self) -> list[str]:
        """
        Validates all required environment variables are set.
        Returns list of missing required env vars.
        """
        import os
        missing = []
        
        for var in self.vars:
            if var.required and not os.getenv(var.name):
                missing.append(var.name)
                logger.warning(f"Missing required environment variable: {var.name} - {var.description}")
                
        return missing 