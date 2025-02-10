from typing import Optional
from pydantic import BaseModel

class SmartPupConfig(BaseModel):
    """Configuration settings for SmartPup"""
    default_model: str = "openai/gpt-4o-mini"
    max_iterations: int = 10
    openrouter_base_url: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    memory_file: str = "memory.json"

# Global config instance
config = SmartPupConfig()

def configure(**kwargs):
    """Update global configuration"""
    global config
    config = SmartPupConfig(**{**config.model_dump(), **kwargs})
