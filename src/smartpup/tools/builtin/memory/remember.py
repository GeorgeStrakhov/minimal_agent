from smartpup.tools.base import BaseTool
from smartpup.tools.env import ToolEnv, EnvVar
from pydantic import BaseModel, Field
import json
import os

class MemoryItem(BaseModel):
    key: str = Field(..., min_length=1, description="The key to store the value under")
    value: str = Field(..., min_length=1, description="The value to remember")

class RememberTool(BaseTool):
    name = "remember"
    description = "Save information to memory for future use"
    
    # Define environment configuration
    env = ToolEnv([
        EnvVar("MEMORY_FILE", "Path to the memory storage file", required=False)
    ])
    
    def __init__(self, memory_file: str = None):
        super().__init__()
        # Use provided file path, env var, or default
        self.memory_file = memory_file or os.getenv("MEMORY_FILE") or "memory.json"
    
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
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    memory = json.load(f)
            else:
                memory = {}
            
            # Update memory
            memory[item.key] = item.value
            
            # Save memory
            with open(self.memory_file, 'w') as f:
                json.dump(memory, f, indent=2)
            
            return f"Successfully saved: {item.key} = {item.value}"
            
        except Exception as e:
            return f"Failed to save to memory: {str(e)}" 