from smartpup.tools.base import BaseTool, ToolConfig
from pydantic import BaseModel, Field
import json
import os
from typing import Optional

class RecallConfig(ToolConfig):
    memory_file: str = Field(
        default_factory=lambda: os.getenv("MEMORY_FILE", "data/memory.json"),
        description="Path to the memory storage file"
    )

class RecallRequest(BaseModel):
    key: str = Field(..., min_length=1, description="The key to recall the value for")

class RecallTool(BaseTool):
    name = "recall"
    description = "Recall information from key-value memory by key"
    config_class = RecallConfig
    
    def __init__(self, config: Optional[RecallConfig] = None):
        super().__init__(config=config)
    
    async def execute(
        self,
        key: str
    ) -> str:
        """
        Retrieve a value from memory
        
        Args:
            key: The key to recall the value for
            
        Returns:
            The remembered value or an error message
        """
        # Validate input
        request = RecallRequest(key=key)
        
        try:
            if not os.path.exists(self.config.memory_file):
                return f"No memory found for key: {request.key}"
            
            with open(self.config.memory_file, 'r') as f:
                memory = json.load(f)
            
            value = memory.get(request.key)
            if value is None:
                return f"No memory found for key: {request.key}"
                
            return f"Remembered value for {request.key}: {value}"
            
        except Exception as e:
            return f"Failed to recall from memory: {str(e)}" 