# Dynamic HTML Crawler Agent

This project provides a flexible agent that can crawl structured objects from HTML files using Google's Gemini model with dynamic tool calling.

## Features

- **Dynamic Configuration**: Define your object structure and field descriptions in JSON configuration files
- **Flexible Field Types**: Support for different data types (string, number, boolean, etc.)
- **Required/Optional Fields**: Mark fields as required or optional
- **Multiple Use Cases**: Easily switch between different crawling scenarios (projects, products, news, etc.)

## Usage

### 1. Create a Configuration File

Create a JSON file that defines the structure of the objects you want to extract:

```json
{
  "function_name": "extract_your_data",
  "function_description": "Extracts a list of your objects from the provided HTML",
  "object_name": "your_objects",
  "object_description": "A list of your object type extracted from HTML",
  "fields": {
    "field_name": {
      "type": "string",
      "description": "Description of what this field contains",
      "required": true
    }
  }
}
```

### 2. Run the Crawler

```python
from crawler_agent.agent import get_structured_json_from_html

# Your configuration
api_key = "your_gemini_api_key"
html_file = "path/to/your/html/file.html"
config_file = "path/to/your/config.json"

# Extract structured data
structured_data = get_structured_json_from_html(
    api_key=api_key,
    html_file_path=html_file,
    config_file_path=config_file
)

print(structured_data)
```

### 3. Example Configurations

The project includes several example configurations:

- **`config_schema.json`**: Project data with company, profit, guarantee information
- **`product_config.json`**: E-commerce products with title, price, rating
- **`news_config.json`**: News articles with headline, author, publish date

## Configuration Schema

Each configuration file should contain:

- **`function_name`**: Name of the extraction function
- **`function_description`**: Description of what the function does
- **`object_name`**: Name of the array containing extracted objects
- **`object_description`**: Description of the object collection
- **`fields`**: Object containing field definitions

### Field Definition

Each field in the `fields` object should have:

- **`type`**: Data type (string, number, boolean, etc.)
- **`description`**: Clear description for the AI model
- **`required`**: Boolean indicating if field is mandatory

## Requirements

- Google Generative AI library (`google-generativeai`)
- Valid Gemini API key
- Python 3.7+

## Installation

```bash
pip install google-generativeai
```

## API Key Setup

Get your API key from [Google AI Studio](https://aistudio.google.com/) and set it in your code or environment variables.