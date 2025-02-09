from ..base_tool import BaseTool
from pydantic import BaseModel, Field
import json
import os

class RecallRequest(BaseModel):
    key: str = Field(..., min_length=1, description="The key to recall the value for")

class RecallTool(BaseTool):
    name = "recall"
    description = "Recall information from memory"
    
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
            memory_file = "memory.json"
            
            if not os.path.exists(memory_file):
                return f"No memory found for key: {request.key}"
            
            with open(memory_file, 'r') as f:
                memory = json.load(f)
            
            value = memory.get(request.key)
            if value is None:
                return f"No memory found for key: {request.key}"
                
            return f"Remembered value for {request.key}: {value}"
            
        except Exception as e:
            return f"Failed to recall from memory: {str(e)}" 