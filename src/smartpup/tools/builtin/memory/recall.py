from smartpup.tools.base import BaseTool
from smartpup.tools.env import ToolEnv, EnvVar
from pydantic import BaseModel, Field
import json
import os

class RecallRequest(BaseModel):
    key: str = Field(..., min_length=1, description="The key to recall the value for")

class RecallTool(BaseTool):
    name = "recall"
    description = "Recall information from key-value memory by key"
    
    # Share the same environment configuration
    env = ToolEnv([
        EnvVar("MEMORY_FILE", "Path to the memory storage file", required=False)
    ])
    
    def __init__(self, memory_file: str = None):
        super().__init__()
        # Use provided file path, env var, or default
        self.memory_file = memory_file or os.getenv("MEMORY_FILE") or "memory.json"
    
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
            if not os.path.exists(self.memory_file):
                return f"No memory found for key: {request.key}"
            
            with open(self.memory_file, 'r') as f:
                memory = json.load(f)
            
            value = memory.get(request.key)
            if value is None:
                return f"No memory found for key: {request.key}"
                
            return f"Remembered value for {request.key}: {value}"
            
        except Exception as e:
            return f"Failed to recall from memory: {str(e)}" 