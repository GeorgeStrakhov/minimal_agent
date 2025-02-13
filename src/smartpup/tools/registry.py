from pathlib import Path
from typing import Dict, Type, List, Union, Optional
import importlib.util
import inspect
from .base import BaseTool, ToolConfig
from loguru import logger

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Type[BaseTool]] = {}
        self._tool_instances: Dict[str, BaseTool] = {}
        
    def discover_tools(self, tools_dir: str = None, tool_names: Optional[List[str]] = None):
        """
        Auto-discover and register tools
        
        Args:
            tools_dir: Optional directory to search for tools. If None, uses built-in tools.
            tool_names: Optional list of specific tool names to load.
        """
        if tools_dir is None:
            # Use the builtin tools directory
            tools_dir = Path(__file__).parent
        else:
            tools_dir = Path(tools_dir)
        logger.info(f"Searching for tools in: {tools_dir}")
        
        # Reset tool registries if we're doing a fresh discovery
        self.tools.clear()
        self._tool_instances.clear()
        
        # Recursively find all Python files
        for file in tools_dir.rglob("*.py"):
            # Skip __init__.py files and utility modules
            if (file.name.startswith("_") or 
                file.name in ["base.py", "registry.py", "env.py"] or
                file.parent.name.startswith("_")):
                logger.debug(f"Skipping file: {file}")
                continue
            
            try:
                # Build the module name relative to the tools directory
                rel_path = file.relative_to(tools_dir)
                module_parts = list(rel_path.parent.parts) + [rel_path.stem]
                module_name = "smartpup.tools." + ".".join(module_parts)
                
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
                        # Create a fresh instance of the tool to pick up current environment variables
                        self.register_tool(obj)
                        
            except Exception as e:
                logger.error(f"Error loading tool from {file}: {e}")
                import traceback
                logger.error(traceback.format_exc())
    
    def register_tool(self, tool_class: Type[BaseTool], config: Optional[ToolConfig] = None):
        """Register a new tool class with optional configuration"""
        try:
            # Only instantiate if we haven't already or if new config provided
            if tool_class.name not in self._tool_instances or config is not None:
                self._tool_instances[tool_class.name] = tool_class(config=config)
            
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
    
    def list_tools(self) -> List[Dict[str, Union[str, Dict]]]:
        """
        Get a list of all available tools with their names, descriptions, and parameters.
        
        Returns:
            List of dictionaries containing tool information with keys:
            - name: Tool name
            - description: Tool description
            - parameters: Dictionary of parameter names and their descriptions
        """
        tool_list = []
        
        for name, instance in self._tool_instances.items():
            # Get the execute method's signature
            from inspect import signature, Parameter
            sig = signature(instance.execute)
            
            # Build parameters info
            parameters = {}
            for param_name, param in sig.parameters.items():
                if param_name != 'self':  # Skip self parameter
                    param_info = {
                        'type': str(param.annotation.__name__) if param.annotation != Parameter.empty else 'any',
                        'description': '',  # Will be populated from docstring if available
                        'default': None if param.default == Parameter.empty else str(param.default)
                    }
                    parameters[param_name] = param_info
            
            tool_info = {
                'name': instance.name,
                'description': instance.description,
                'parameters': parameters
            }
            tool_list.append(tool_info)
            
        return tool_list

    def configure_tool(self, tool_name: str, config: Dict):
        """Configure an existing tool with new settings"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found")
        
        tool_class = self.tools[tool_name]
        if not tool_class.config_class:
            raise ValueError(f"Tool {tool_name} does not support configuration")
        
        # Create config instance from dict
        config_instance = tool_class.config_class.model_validate(config)
        
        # Re-register tool with new config
        self.register_tool(tool_class, config=config_instance) 