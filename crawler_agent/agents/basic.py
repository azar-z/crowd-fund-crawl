"""
BasicAgent implementation for simple structured data extraction from HTML without tool calling.
"""

import json
import re
import google.generativeai as genai
from crawler_agent.agents.base import BaseCrawlerAgent


class BasicAgent(BaseCrawlerAgent):
    """
    Basic implementation of CrawlerAgent for extracting structured data from HTML
    using simple prompting without function calling tools.
    """
    
    def process_html(self, html_file_path: str, config_file_path: str):
        """
        Process HTML content and extract structured data using basic prompting.
        
        Args:
            html_file_path (str): Path to the HTML file to process
            config_file_path (str): Path to the configuration file
            
        Returns:
            Structured data extracted from the HTML
        """
        # Load configuration from JSON file
        with open(config_file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Define system prompt for Basic Agent role
        system_prompt = """You are a Web Data Extraction Agent."""

        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_prompt
        )

        # Build field descriptions for the prompt
        field_descriptions = []
        for field_name, field_config in config["fields"].items():
            field_desc = f"- {field_name}: {field_config['description']}"
            if field_config.get("required", False):
                field_desc += " (required)"
            field_descriptions.append(field_desc)

        object_name = config.get("object_name", "data")
        
        prompt = f"""Extract the {config['object_description']} from the following HTML content.

        TARGET FIELDS TO EXTRACT:
        {chr(10).join(field_descriptions)}
        
        Please provide the extracted data in this JSON format:
        {{
            "{object_name}": {{
                "field_name": "extracted_value_or_null"
            }}
        }}
        
        - Return only the JSON response, no additional text
        
        HTML CONTENT:
        {html_content}"""
        
        response = model.generate_content(prompt)
        
        # Parse JSON response
        try:
            response_text = response.text.strip()
            # Clean up response text (remove code blocks if present)
            if "```json" in response_text:
                response_text = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL).group(1)
            elif "```" in response_text:
                response_text = re.search(r'```\s*(.*?)\s*```', response_text, re.DOTALL).group(1)
            
            # Parse JSON
            result = json.loads(response_text)
            return result
            
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"Failed to parse JSON response: {e}")
            print(f"Raw response: {response.text}")
            # Return basic structure with null values as fallback
            return {
                object_name: {field_name: None for field_name in config["fields"].keys()}
            }
