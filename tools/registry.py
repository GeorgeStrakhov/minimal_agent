from pathlib import Path
from typing import Dict, Type, List, Union, Optional
import importlib.util
import inspect
from .base_tool import BaseTool
from loguru import logger

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Type[BaseTool]] = {}
        self._tool_instances: Dict[str, BaseTool] = {}
        
    def discover_tools(self, tools_dir: str = "tools", tool_names: Optional[List[str]] = None):
        """
        Auto-discover and register tools
        
        Args:
            tools_dir: Directory to search for tools
            tool_names: Optional list of specific tool names to load. If None, loads all tools.
        """
        tools_path = Path(tools_dir).resolve()
        logger.info(f"Searching for tools in: {tools_path}")
        
        # Reset tool registries if we're doing a fresh discovery
        self.tools.clear()
        self._tool_instances.clear()
        
        # Recursively find all Python files
        for file in tools_path.rglob("*.py"):
            # Skip __init__.py and base files
            if file.name.startswith("_") or file.name == "base_tool.py" or file.name == "registry.py":
                logger.debug(f"Skipping file: {file}")
                continue
            
            try:
                # Load the module
                module_name = str(file.relative_to(tools_path).with_suffix("")).replace("/", ".")
                logger.debug(f"Attempting to load module: {module_name} from {file}")
                
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
                        
                        # Skip if we have a tool_names filter and this tool isn't in it
                        if tool_names and obj.name not in tool_names:
                            logger.debug(f"Skipping tool {obj.name} - not in requested tools")
                            continue
                            
                        logger.info(f"Found tool class: {name} with tool name: {obj.name}")
                        self.register_tool(obj)
                        
            except Exception as e:
                logger.error(f"Error loading tool from {file}: {e}")
                import traceback
                logger.error(traceback.format_exc())
    
    def register_tool(self, tool_class: Type[BaseTool]):
        """Register a new tool class"""
        try:
            # Only instantiate if we haven't already
            if tool_class.name not in self._tool_instances:
                self._tool_instances[tool_class.name] = tool_class()
            
            self.tools[tool_class.name] = tool_class
            logger.info(f"Successfully registered tool: {tool_class.name}")
        except Exception as e:
            logger.error(f"Failed to register tool {tool_class.__name__}: {e}")
    
    def get_tools(self, names: Optional[List[str]] = None) -> Dict[str, Dict]:
        """
        Get tool configurations for specified tools or all tools
        
        Args:
            names: Optional list of tool names to return. If None, returns all tools.
            
        Returns:
            Dictionary containing both schemas and functions for the tools
        """
        tool_dict = {}
        
        for name, instance in self._tool_instances.items():
            if names is None or name in names:
                tool_dict[name] = {
                    'schema': instance.get_schema(),
                    'function': instance.execute
                }
                
        return tool_dict
    
    def get_schemas(self, names: Optional[List[str]] = None) -> list:
        """Get OpenAI tool schemas for specified tools or all tools"""
        return [
            instance.get_schema() 
            for name, instance in self._tool_instances.items()
            if names is None or name in names
        ]
    
    def get_tool_functions(self, names: Optional[List[str]] = None) -> Dict[str, callable]:
        """Get map of tool names to their execute functions"""
        return {
            name: instance.execute
            for name, instance in self._tool_instances.items()
            if names is None or name in names
        } 