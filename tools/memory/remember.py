from ..base_tool import BaseTool
from typing import Any
import json
import os

class RememberTool(BaseTool):
    name = "remember"
    description = "Save information to memory for future use"
    
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
        try:
            memory_file = "memory.json"
            
            # Load existing memory
            if os.path.exists(memory_file):
                with open(memory_file, 'r') as f:
                    memory = json.load(f)
            else:
                memory = {}
            
            # Update memory
            memory[key] = value
            
            # Save memory
            with open(memory_file, 'w') as f:
                json.dump(memory, f, indent=2)
            
            return f"Successfully saved: {key} = {value}"
            
        except Exception as e:
            return f"Failed to save to memory: {str(e)}" 