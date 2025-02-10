from typing import Optional, Dict, Any

class PupError(Exception):
    """Base error class for Pup-related errors"""
    
    # Core error types
    TECHNICAL = "technical"  # System/API errors
    COGNITIVE = "cognitive"  # LLM confusion/uncertainty
    
    # Specific error subtypes
    INVALID_JSON = "invalid_json"
    SCHEMA_VIOLATION = "schema_violation"
    MISSING_REQUIREMENTS = "missing_requirements"
    UNCERTAIN = "uncertain"
    
    def __init__(self, 
                 type: str, 
                 message: str, 
                 subtype: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        self.type = type
        self.subtype = subtype
        self.message = message
        self.details = details
        super().__init__(f"{type}({subtype}): {message}" if subtype else f"{type}: {message}") 