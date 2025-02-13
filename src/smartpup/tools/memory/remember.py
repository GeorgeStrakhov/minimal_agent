from smartpup.tools.base import BaseTool, ToolConfig
from pydantic import BaseModel, Field
import json
import os
from typing import Optional

class MemoryConfig(ToolConfig):
    memory_file: str = Field(
        default_factory=lambda: os.getenv("MEMORY_FILE", "data/memory.json"),
        description="Path to the memory storage file"
    )

class MemoryItem(BaseModel):
    key: str = Field(..., min_length=1, description="The key to store the value under")
    value: str = Field(..., min_length=1, description="The value to remember")

class RememberTool(BaseTool):
    name = "remember"
    description = "Save information to memory for future use"
    config_class = MemoryConfig
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        super().__init__(config=config)
    
    async def execute(
        self,
        key: str,
        value: str
    ) -> str:
        """
        Save a value to memory
        
        Args:
            key: The key to store the value under
            value: The value to remember
            
        Returns:
            A confirmation message
        """
        # Validate inputs
        item = MemoryItem(key=key, value=value)
        
        try:
            # Load existing memory
            if os.path.exists(self.config.memory_file):
                with open(self.config.memory_file, 'r') as f:
                    memory = json.load(f)
            else:
                memory = {}
            
            # Update memory
            memory[item.key] = item.value
            
            # Save memory
            with open(self.config.memory_file, 'w') as f:
                json.dump(memory, f, indent=2)
            
            return f"Successfully saved: {item.key} = {item.value}"
            
        except Exception as e:
            return f"Failed to save to memory: {str(e)}" 