"""
Main script to test the BasicCrawlerAgent.
"""

import os
from dotenv import load_dotenv
from crawler_agent.agents.simple import SimpleCrawlerAgent


def main():
    """Main function to test the BasicCrawlerAgent."""
    # Load environment variables from .env file if it exists
    load_dotenv()

    # Get API key from environment variable
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set. Please set it with your API key.")

    # Initialize the BasicCrawlerAgent
    crawler = SimpleCrawlerAgent(api_key=api_key)

    # Define file paths
    html_file = "single_samples/dongi.html"
    config_file = "configs/single_project_config.json"
    output_file = "output.json"

    try:
        # Process HTML and save results
        print("Starting HTML processing...")
        crawler.process_and_save(
            html_file_path=html_file,
            config_file_path=config_file,
            output_file=output_file
        )
        print("Processing completed successfully!")
        
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
    except Exception as e:
        print(f"Error during processing: {e}")


if __name__ == "__main__":
    main()
