import google.generativeai as genai
from google.generativeai.types import Tool, FunctionDeclaration
import json
import os
from dotenv import load_dotenv


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


def get_structured_json_from_html(api_key, html_file_path, config_file_path):
    genai.configure(
        api_key=api_key,
        transport="rest",
        # client_options=ClientOptions(api_endpoint="https://openrouter.ai/api/v1")
        # client_options=ClientOptions(api_endpoint="https://api.gapgpt.app/")
    )

    # Load configuration from JSON file
    with open(config_file_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Create dynamic function declaration from config
    function_declaration = create_function_declaration_from_config(config)
    
    tools = [
        Tool(
            function_declarations=[function_declaration]
        )
    ]

    model = genai.GenerativeModel(
        model_name='gemini-2.0-flash',
        tools=tools
    )

    prompt = f"Use the function `{config['function_name']}` to return the {config['object_description']} from the following HTML. " \
             f"Only use the function.\n\n\n {html_content}"
    response = model.generate_content(prompt)
    print(response)
    function_call = response.candidates[0].content.parts[0].function_call
    return function_call.args


if __name__ == "__main__":
    # Load environment variables from .env file if it exists
    load_dotenv()

    # Get API key from environment variable
    my_api_key = os.getenv("GEMINI_API_KEY")
    if not my_api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set. Please set it with your API key.")

    html_file = "single_samples/dongi.html"
    config_file = "configs/single_project_config.json"  # Configuration file path

    structured_data = get_structured_json_from_html(
        api_key=my_api_key,
        html_file_path=html_file,
        config_file_path=config_file
    )

    if structured_data:
        print(dict(structured_data))
    else:
        print("Tool was not used!")
