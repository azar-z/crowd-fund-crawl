"""
BasicCrawlerAgent implementation for structured data extraction from HTML.
"""

import json
from google.generativeai.types import Tool
import google.generativeai as genai
from crawler_agent.agents.base import BaseCrawlerAgent
from crawler_agent.utils import create_function_declaration_from_config


class SimpleCrawlerAgent(BaseCrawlerAgent):
    """
    Basic implementation of CrawlerAgent for extracting structured data from HTML
    using Google's Generative AI with dynamic function declarations.
    """
    
    def process_html(self, html_file_path: str, config_file_path: str):
        """
        Process HTML content and extract structured data based on configuration.
        
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

        # Create dynamic function declaration from config
        function_declaration = create_function_declaration_from_config(config)
        
        tools = [
            Tool(
                function_declarations=[function_declaration]
            )
        ]

        model = genai.GenerativeModel(
            model_name=self.model_name,
            tools=tools
        )

        prompt = f"Use the function `{config['function_name']}` to return the {config['object_description']} from the following HTML. " \
                 f"Only use the function.\n\n\n {html_content}"
        
        response = model.generate_content(prompt)

        function_call = response.candidates[0].content.parts[0].function_call
        return function_call.args
