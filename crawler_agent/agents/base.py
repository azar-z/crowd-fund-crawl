"""
Base CrawlerAgent class for web crawling operations.
"""
import json

import google.generativeai as genai
from abc import ABC, abstractmethod

from crawler_agent.utils import proto_to_dict


class BaseCrawlerAgent(ABC):
    """
    Base abstract class for crawler agents.
    
    This class provides common functionality for web crawling operations
    using Google's Generative AI.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the CrawlerAgent with API key.
        
        Args:
            api_key (str): The API key for Google Generative AI
        """
        if not api_key:
            raise ValueError("API key cannot be empty")
        
        self.api_key = api_key
        self._configure_genai()
    
    def _configure_genai(self):
        """Configure the Google Generative AI with the provided API key."""
        genai.configure(
            api_key=self.api_key,
            transport="rest",
            # client_options=ClientOptions(api_endpoint="https://openrouter.ai/api/v1")
            # client_options=ClientOptions(api_endpoint="https://api.gapgpt.app/")
        )
    
    @abstractmethod
    def process_html(self, html_file_path: str, config_file_path: str):
        """
        Abstract method to process HTML content.
        
        Args:
            html_file_path (str): Path to the HTML file to process
            config_file_path (str): Path to the configuration file
            
        Returns:
            Processed data from the HTML
        """
        pass

    def save_results_to_file(self, structured_data, output_file: str = "output.json"):
        """
        Save structured data to a JSON file.

        Args:
            structured_data: The structured data to save
            output_file (str): Output file path (default: "output.json")
        """
        if structured_data:
            with open(output_file, "w", encoding="utf-8") as outfile:
                json.dump(proto_to_dict(structured_data), outfile, indent=2, ensure_ascii=False)
            print(f"Results saved successfully to {output_file}!")
        else:
            print("No data to save - tool was not used!")

    def process_and_save(self, html_file_path: str, config_file_path: str, output_file: str = "output.json"):
        """
        Process HTML and save results to file in one operation.

        Args:
            html_file_path (str): Path to the HTML file to process
            config_file_path (str): Path to the configuration file
            output_file (str): Output file path (default: "output.json")
        """
        structured_data = self.process_html(html_file_path, config_file_path)
        self.save_results_to_file(structured_data, output_file)
