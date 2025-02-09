from ..base_tool import BaseTool
import json
import os

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
        try:
            memory_file = "memory.json"
            
            if not os.path.exists(memory_file):
                return f"No memory found for key: {key}"
            
            with open(memory_file, 'r') as f:
                memory = json.load(f)
            
            value = memory.get(key)
            if value is None:
                return f"No memory found for key: {key}"
                
            return f"Remembered value for {key}: {value}"
            
        except Exception as e:
            return f"Failed to recall from memory: {str(e)}" 