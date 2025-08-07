"""
Utility functions for the crawler agent.
"""

from google.generativeai.types import FunctionDeclaration


def create_function_declaration_from_config(config):
    """
    Creates a FunctionDeclaration from a JSON configuration.
    
    Args:
        config (dict): Configuration dictionary containing function details and field definitions
        
    Returns:
        FunctionDeclaration: The dynamically created function declaration
    """
    # Build the description with field details
    field_descriptions = []
    for field_name, field_config in config["fields"].items():
        field_descriptions.append(f"- {field_name}: {field_config['description']}")
    
    full_description = config["function_description"]
    if field_descriptions:
        if config.get("is_array", True):  # Default to array for backward compatibility
            full_description += ". Each object must include:\n" + "\n".join(field_descriptions)
        else:
            full_description += ". The object must include:\n" + "\n".join(field_descriptions)
    
    # Build the properties schema
    properties = {}
    required_fields = []
    
    for field_name, field_config in config["fields"].items():
        properties[field_name] = {"type": field_config["type"]}
        if field_config.get("required", False):
            required_fields.append(field_name)
    
    # Determine if we want an array or single object
    is_array = config.get("is_array", True)  # Default to array for backward compatibility
    
    if is_array:
        # Original array structure
        object_schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": properties,
                "required": required_fields
            }
        }
    else:
        # Single object structure
        object_schema = {
            "type": "object",
            "properties": properties,
            "required": required_fields
        }
    
    # Create the function declaration
    function_declaration = FunctionDeclaration(
        name=config["function_name"],
        description=full_description,
        parameters={
            "type": "object",
            "properties": {
                config["object_name"]: object_schema
            },
            "required": [config["object_name"]]
        }
    )
    
    return function_declaration


def proto_to_dict(obj):
    """
    Convert protobuf objects to regular Python dictionaries recursively.
    
    Args:
        obj: The object to convert (can be protobuf message, dict, list, or primitive)
        
    Returns:
        Converted object as regular Python data structures
    """
    if hasattr(obj, 'items'):
        return {k: proto_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [proto_to_dict(i) for i in obj]
    elif hasattr(obj, 'DESCRIPTOR'):  # protobuf message
        result = {}
        for field in obj.DESCRIPTOR.fields:
            value = getattr(obj, field.name)
            if value is not None:
                result[field.name] = proto_to_dict(value)
        return result
    else:
        return obj
