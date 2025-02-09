from typing import Any, Dict, Optional, get_type_hints, Type, Union, _GenericAlias
from pydantic import BaseModel, create_model
import inspect
import docstring_parser
from loguru import logger

class BaseTool:
    name: str
    description: str
    
    def __init__(self):
        if not hasattr(self, 'name') or not hasattr(self, 'description'):
            raise ValueError(f"Tool {self.__class__.__name__} must define 'name' and 'description'")
    
    async def execute(self, **kwargs) -> Any:
        """Override this method to implement the tool's functionality"""
        raise NotImplementedError
    
    @classmethod
    def _get_type_schema(cls, param_type: Type) -> Dict[str, Any]:
        """Convert Python type to JSON schema type"""
        if param_type == str:
            return {"type": "string"}
        elif param_type == int:
            return {"type": "integer"}
        elif param_type == float:
            return {"type": "number"}
        elif param_type == bool:
            return {"type": "boolean"}
        elif isinstance(param_type, _GenericAlias):
            # Handle Optional types (Union[Type, None])
            if (param_type.__origin__ is Union and 
                len(param_type.__args__) == 2 and 
                type(None) in param_type.__args__):
                inner_type = next(t for t in param_type.__args__ if t is not type(None))
                return cls._get_type_schema(inner_type)
        else:
            logger.warning(f"Unsupported type {param_type}, defaulting to string")
            return {"type": "string"}
    
    @classmethod
    def _get_parameter_schema(cls, hints: Dict[str, Type], docstring: str) -> Dict[str, Any]:
        """Generate JSON Schema for parameters based on type hints and docstring"""
        parameters = {}
        doc = docstring_parser.parse(docstring)
        param_docs = {param.arg_name: param.description for param in doc.params}
        
        # Get the execute method's signature to check for default values
        sig = inspect.signature(cls.execute)
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':  # Skip self parameter
                continue
                
            param_schema = {
                "description": param_docs.get(param_name, f"Parameter {param_name}"),
            }
            
            # Get type information
            param_type = hints.get(param_name, str)
            param_schema.update(cls._get_type_schema(param_type))
            
            # Check if parameter has a default value
            if param.default is not param.empty:
                if param.default is not None:  # Only add default if it's not None
                    param_schema["default"] = param.default
            
            parameters[param_name] = param_schema
            
        return parameters, [
            name for name, param in sig.parameters.items()
            if param.default is param.empty and name != 'self'
        ]
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """
        Auto-generates OpenAI tool schema from the execute method's type hints 
        and docstring
        """
        # Get the execute method
        execute_method = cls.execute
        
        # Get type hints and docstring
        hints = get_type_hints(execute_method)
        doc = inspect.getdoc(execute_method)
        
        if not doc:
            doc = "No description provided"
        
        # Parse the main description from the docstring
        parsed_doc = docstring_parser.parse(doc)
        description = parsed_doc.short_description or cls.description
        
        # Generate parameters schema
        parameters, required = cls._get_parameter_schema(hints, doc)
        
        # Create the full schema
        schema = {
            "type": "function",
            "function": {
                "name": cls.name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": parameters,
                    "required": required
                }
            }
        }
        
        return schema 