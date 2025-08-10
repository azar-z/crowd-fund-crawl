"""
AdvancedCrawlerAgent implementation with multiple accuracy improvement techniques.
"""

import json
import re
from typing import Dict, Any, List, Tuple
from collections import Counter
from google.generativeai.types import Tool
import google.generativeai as genai
from crawler_agent.agents.base import BaseCrawlerAgent
from crawler_agent.utils import create_function_declaration_from_config, proto_to_dict


class AdvancedCrawlerAgent(BaseCrawlerAgent):
    """
    Advanced implementation of CrawlerAgent with multiple accuracy improvements:
    - HTML preprocessing to identify relevant sections
    - Verification step with retry mechanism
    - Multiple extraction attempts with voting
    - Confidence scoring and error recovery
    """
    
    def __init__(self, api_key: str, model_name: str = 'gemini-2.0-flash-lite', 
                 max_retries: int = 3, voting_rounds: int = 3):
        """
        Initialize the AdvancedCrawlerAgent.
        
        Args:
            api_key (str): The API key for Google Generative AI
            model_name (str): The name of the model to use (default: 'gemini-2.0-flash-lite')
            max_retries (int): Maximum number of retry attempts for verification
            voting_rounds (int): Number of extraction rounds for voting
        """
        super().__init__(api_key, model_name)
        self.max_retries = max_retries
        self.voting_rounds = voting_rounds
        self.debug_mode = True  # For comparison purposes
    
    def _extract_relevant_html_sections(self, html_content: str, config: Dict) -> str:
        """
        Extract relevant sections of HTML based on project data patterns.
        
        Args:
            html_content (str): Full HTML content
            config (Dict): Configuration containing field descriptions
            
        Returns:
            str: Filtered HTML content with relevant sections
        """
        if self.debug_mode:
            print("🔍 Step 1: Extracting relevant HTML sections...")
        
        # Create a simple model for HTML section identification
        model = genai.GenerativeModel(model_name=self.model_name)
        
        # Build detailed field information from config
        field_details = []
        for field_name, field_config in config["fields"].items():
            field_info = f"- {field_name}: {field_config['description']}"
            if 'type' in field_config:
                field_info += f" (type: {field_config['type']})"
            if 'examples' in field_config:
                field_info += f" (examples: {', '.join(field_config['examples'])})"
            field_details.append(field_info)
        
        fields_description = "\n".join(field_details)
        
        # Get additional context from config
        object_description = config.get('object_description', 'target data')
        function_description = config.get('function_description', 'Extract target information')
        
        prompt = f"""
        Analyze this HTML and identify the main content section that contains {object_description}.
        
        TARGET EXTRACTION: {function_description}
        
        SPECIFIC FIELDS TO LOOK FOR:
        {fields_description}
        
        Your task is to identify and return ONLY the HTML section that contains the actual data for these fields.
        
        REMOVE these irrelevant sections:
        - Navigation menus and sidebars
        - Headers and footers  
        - Advertisements and promotional content
        - Scripts, styles, and metadata
        - Comments and user interactions
        - Unrelated content not containing the target data
        
        KEEP these relevant sections:
        - Main content area with target details
        - Data tables or lists with target information
        - Text blocks containing the specific fields mentioned above
        - Images or media related to the target
        
        Focus on content that likely contains: {', '.join(config["fields"].keys())}
        
        HTML:
        {html_content}
        """
        
        try:
            response = model.generate_content(prompt)
            filtered_html = response.text
            
            # Fallback: if response is too short, use pattern-based filtering
            if len(filtered_html) < 200:
                filtered_html = self._pattern_based_filtering(html_content)
                
            if self.debug_mode:
                print(f"   📝 Reduced HTML from {len(html_content)} to {len(filtered_html)} characters")
                
            return filtered_html
            
        except Exception as e:
            if self.debug_mode:
                print(f"   ⚠️ HTML filtering failed: {e}, using pattern-based fallback")
            return self._pattern_based_filtering(html_content)
    
    def _pattern_based_filtering(self, html_content: str) -> str:
        """
        Fallback pattern-based HTML filtering.
        
        Args:
            html_content (str): Full HTML content
            
        Returns:
            str: Filtered HTML content
        """
        # Remove script and style tags
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
        
        # Look for main content patterns
        patterns = [
            r'<main[^>]*>.*?</main>',
            r'<article[^>]*>.*?</article>',
            r'<div[^>]*class[^>]*(?:content|main|project|detail)[^>]*>.*?</div>',
            r'<section[^>]*>.*?</section>'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content, flags=re.DOTALL | re.IGNORECASE)
            if matches:
                return matches[0]
        
        # If no patterns match, return middle portion of HTML
        lines = html_content.split('\n')
        start = len(lines) // 4
        end = 3 * len(lines) // 4
        return '\n'.join(lines[start:end])
    
    def _extract_data_with_function(self, html_content: str, config: Dict) -> Any:
        """
        Extract data using function calling (similar to simple agent).
        
        Args:
            html_content (str): HTML content to process
            config (Dict): Configuration for extraction
            
        Returns:
            Extracted data or None if failed
        """
        try:
            function_declaration = create_function_declaration_from_config(config)
            
            tools = [Tool(function_declarations=[function_declaration])]
            model = genai.GenerativeModel(model_name=self.model_name, tools=tools)
            
            prompt = f"""Use the function `{config['function_name']}` to return the {config['object_description']} from the following HTML.
            Only use the function and be very careful to extract accurate data.
            
            HTML:
            {html_content}"""
            
            response = model.generate_content(prompt)
            
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        return part.function_call.args
            
            return None
            
        except Exception as e:
            if self.debug_mode:
                print(f"   ⚠️ Function extraction failed: {e}")
            return None
    
    def _verify_extraction(self, extracted_data: Any, config: Dict, html_content: str) -> Tuple[bool, float]:
        """
        Verify the quality of extracted data.
        
        Args:
            extracted_data: The extracted data to verify
            config (Dict): Configuration for verification
            html_content (str): Original HTML content
            
        Returns:
            Tuple[bool, float]: (is_valid, confidence_score)
        """
        if not extracted_data:
            return False, 0.0
        
        try:
            data_dict = proto_to_dict(extracted_data)
            if self.debug_mode:
                print(f"   🔍 Verifying extraction: {data_dict}")
            
            # Create verification prompt
            model = genai.GenerativeModel(model_name=self.model_name)
            
            prompt = f"""
            Verify if this extracted data is accurate based on the HTML content.
            
            Extracted Data:
            {json.dumps(data_dict, indent=2, ensure_ascii=False)}
            
            HTML Content:
            {html_content}
            
            Check for:
            1. Data accuracy - are the values correct?
            2. Completeness - are required fields present?
            3. Consistency - do the values make sense together?
            
            Respond with:
            - "VALID" if the data is accurate and complete
            - "INVALID" if there are significant errors or missing required data
            - Include a confidence score from 0.0 to 1.0
            
            Format: VALID/INVALID|confidence_score|brief_reason
            """
            
            response = model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Parse response
            parts = response_text.split('|')
            if len(parts) >= 2:
                validity = parts[0].strip().upper() == 'VALID'
                try:
                    confidence = float(parts[1].strip())
                except ValueError:
                    confidence = 0.5
                
                if self.debug_mode:
                    reason = parts[2] if len(parts) > 2 else "No reason provided"
                    print(f"   📋 Verification: {validity}, confidence: {confidence:.2f}, reason: {reason}")
                
                return validity, confidence
            
            return False, 0.0
            
        except Exception as e:
            if self.debug_mode:
                print(f"   ⚠️ Verification failed: {e}")
            return False, 0.0
    
    def _extract_with_retry(self, html_content: str, config: Dict) -> Tuple[Any, float]:
        """
        Extract data with verification and retry mechanism.
        
        Args:
            html_content (str): HTML content to process
            config (Dict): Configuration for extraction
            
        Returns:
            Tuple[Any, float]: (best_extraction, confidence_score)
        """
        if self.debug_mode:
            print("🔄 Step 2: Extracting with verification and retry...")
        
        best_extraction = None
        best_confidence = 0.0
        
        for attempt in range(self.max_retries):
            if self.debug_mode:
                print(f"   🎯 Attempt {attempt + 1}/{self.max_retries}")
            
            # Extract data
            extracted = self._extract_data_with_function(html_content, config)
            
            if extracted:
                # Verify extraction
                is_valid, confidence = self._verify_extraction(extracted, config, html_content)
                
                if is_valid and confidence > best_confidence:
                    best_extraction = extracted
                    best_confidence = confidence
                    
                    # If we have high confidence, break early
                    if confidence > 0.8:
                        if self.debug_mode:
                            print(f"   ✅ High confidence achieved: {confidence:.2f}")
                        break
        
        return best_extraction, best_confidence
    
    def _flatten_dict(self, data: Dict, parent_key: str = '', sep: str = '.') -> Dict:
        """
        Flatten nested dictionary for voting.
        
        Args:
            data (Dict): Dictionary to flatten
            parent_key (str): Parent key for nested items
            sep (str): Separator for nested keys
            
        Returns:
            Dict: Flattened dictionary
        """
        items = []
        for k, v in data.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def _unflatten_dict(self, data: Dict, sep: str = '.') -> Dict:
        """
        Unflatten dictionary after voting.
        
        Args:
            data (Dict): Flattened dictionary
            sep (str): Separator used in flattening
            
        Returns:
            Dict: Unflattened dictionary
        """
        result = {}
        for key, value in data.items():
            parts = key.split(sep)
            d = result
            for part in parts[:-1]:
                if part not in d:
                    d[part] = {}
                d = d[part]
            d[parts[-1]] = value
        return result
    
    def _vote_on_extractions(self, extractions: List[Any]) -> Any:
        """
        Vote on multiple extractions to get the best result.
        
        Args:
            extractions (List[Any]): List of extracted data
            
        Returns:
            Any: Best extraction based on voting
        """
        if self.debug_mode:
            print("🗳️ Step 3: Voting on multiple extractions...")
        
        if not extractions:
            return None
        
        # Convert all extractions to dictionaries and flatten them
        flattened_extractions = []
        for extraction in extractions:
            if extraction:
                try:
                    data_dict = proto_to_dict(extraction)
                    flattened = self._flatten_dict(data_dict)
                    flattened_extractions.append(flattened)
                except Exception as e:
                    if self.debug_mode:
                        print(f"   ⚠️ Failed to process extraction: {e}")
                    continue
        
        if not flattened_extractions:
            return None
        
        # Vote on each field
        voted_result = {}
        all_keys = set()
        for extraction in flattened_extractions:
            all_keys.update(extraction.keys())
        
        for key in all_keys:
            values = []
            for extraction in flattened_extractions:
                if key in extraction and extraction[key] is not None:
                    values.append(extraction[key])
            
            if values:
                # For strings and numbers, use most common value
                if all(isinstance(v, (str, int, float)) for v in values):
                    voted_value = Counter(values).most_common(1)[0][0]
                else:
                    # For other types, use first valid value
                    voted_value = values[0]
                
                voted_result[key] = voted_value
                
                if self.debug_mode:
                    print(f"   📊 {key}: {voted_value} (from {len(values)} votes)")
        
        # Unflatten the result
        final_result = self._unflatten_dict(voted_result)
        
        if self.debug_mode:
            print(f"   ✅ Final voted result: {final_result}")
        
        return final_result
    
    def process_html(self, html_file_path: str, config_file_path: str):
        """
        Process HTML content with advanced accuracy improvements.
        
        Args:
            html_file_path (str): Path to the HTML file to process
            config_file_path (str): Path to the configuration file
            
        Returns:
            Structured data extracted from the HTML with high accuracy
        """
        if self.debug_mode:
            print("🚀 Starting Advanced HTML Processing...")
        
        # Load configuration and HTML
        with open(config_file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Step 1: Extract relevant HTML sections
        # filtered_html = self._extract_relevant_html_sections(html_content, config)
        
        # Step 2: Multiple extraction rounds with voting
        extractions = []
        confidences = []
        
        for round_num in range(self.voting_rounds):
            if self.debug_mode:
                print(f"🎲 Extraction round {round_num + 1}/{self.voting_rounds}")
            
            # Use slightly different approaches for each round
            if round_num == 0:
                # First round: use filtered HTML
                extraction, confidence = self._extract_with_retry(html_content, config)
            elif round_num == 1:
                # Second round: use original HTML with focused prompt
                extraction, confidence = self._extract_with_retry(html_content, config)
            else:
                # Third round: use filtered HTML with emphasis on completeness
                modified_config = config.copy()
                modified_config["function_description"] += " Pay special attention to extracting ALL required fields completely and accurately."
                extraction, confidence = self._extract_with_retry(html_content, modified_config)
            
            if extraction:
                extractions.append(extraction)
                confidences.append(confidence)
        
        # Step 3: Vote on the best result
        if extractions:
            final_result = self._vote_on_extractions(extractions)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            if self.debug_mode:
                print(f"🎯 Processing complete! Average confidence: {avg_confidence:.2f}")
                print(f"📊 Successful extractions: {len(extractions)}/{self.voting_rounds}")
            
            return final_result
        else:
            if self.debug_mode:
                print("❌ All extraction attempts failed!")
            return None
