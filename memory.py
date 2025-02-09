import json
import os
from typing import Dict, Any
from loguru import logger

class FileMemory:
    def __init__(self, file_path: str = "memory.json"):
        self.file_path = file_path
        self._ensure_memory_file()

    def _ensure_memory_file(self):
        """Create memory file if it doesn't exist"""
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                json.dump({}, f)

    def save(self, key: str, value: Any) -> str:
        """Save a value to memory"""
        try:
            with open(self.file_path, 'r') as f:
                memory = json.load(f)
            
            memory[key] = value
            
            with open(self.file_path, 'w') as f:
                json.dump(memory, f, indent=2)
            
            return f"Successfully saved: {key} = {value}"
        except Exception as e:
            logger.error("Error saving to memory: {}", e)
            return f"Failed to save to memory: {str(e)}"

    def get(self, key: str) -> Any:
        """Retrieve a value from memory"""
        try:
            with open(self.file_path, 'r') as f:
                memory = json.load(f)
            return memory.get(key, None)
        except Exception as e:
            logger.error("Error reading from memory: {}", e)
            return None

    def get_all(self) -> Dict[str, Any]:
        """Get all stored memory"""
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error("Error reading memory: {}", e)
            return {} 