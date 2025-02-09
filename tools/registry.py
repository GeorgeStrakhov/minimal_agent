from pathlib import Path
from typing import Dict, Type
import importlib.util
import inspect
from .base_tool import BaseTool
from loguru import logger

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Type[BaseTool]] = {}
        
    def discover_tools(self, tools_dir: str = "tools"):
        """Auto-discover and register all tool classes"""
        tools_path = Path(tools_dir).resolve()  # Get absolute path
        logger.info(f"Searching for tools in: {tools_path}")
        
        # Recursively find all Python files
        for file in tools_path.rglob("*.py"):
            # Skip __init__.py and base_tool.py
            if file.name.startswith("_") or file.name == "base_tool.py" or file.name == "registry.py":
                logger.debug(f"Skipping file: {file}")
                continue
            
            logger.info(f"Loading tool file: {file}")
            
            try:
                # Load the module
                module_name = f"tools.{'.'.join(file.relative_to(tools_path).with_suffix('').parts)}"
                logger.debug(f"Module name: {module_name}")
                
                spec = importlib.util.spec_from_file_location(module_name, str(file))
                if spec is None or spec.loader is None:
                    logger.warning(f"Could not get spec for {file}")
                    continue
                    
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find all BaseTool subclasses in the module
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseTool) and 
                        obj != BaseTool):
                        logger.info(f"Found tool class: {name} with tool name: {obj.name}")
                        self.register_tool(obj)
                        
            except Exception as e:
                logger.error(f"Error loading tool from {file}: {e}")
                import traceback
                logger.error(traceback.format_exc())
    
    def register_tool(self, tool_class: Type[BaseTool]):
        """Register a new tool class"""
        try:
            tool = tool_class()  # Test instantiation
            self.tools[tool_class.name] = tool_class
            logger.info(f"Successfully registered tool: {tool_class.name}")
        except Exception as e:
            logger.error(f"Failed to register tool {tool_class.__name__}: {e}")
    
    def get_schemas(self) -> list:
        """Get OpenAI tool schemas for all registered tools"""
        return [tool.get_schema() for tool in self.tools.values()]
    
    def get_tool_functions(self) -> Dict[str, callable]:
        """Get map of tool names to their execute functions"""
        return {
            name: tool().execute for name, tool in self.tools.items()
        } 