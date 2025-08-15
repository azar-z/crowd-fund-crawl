"""
ExpertAgent implementation with multiple accuracy improvement techniques.
"""

import json
import re
from typing import Dict, Any, List, Tuple
from google.generativeai.types import Tool
import google.generativeai as genai
from crawler_agent.agents.base import BaseCrawlerAgent
from crawler_agent.utils import create_function_declaration_from_config, proto_to_dict


class ExpertAgent(BaseCrawlerAgent):
    """
    Expert implementation of CrawlerAgent with improved accuracy techniques:
    - Efficient HTML cleaning (removing noise while preserving content)
    - Enhanced prompts with field-specific guidance for each round
    - Smart field validation with quality scoring
    - Intelligent merging of multiple extractions with confidence weighting
    - Reduced processing time while maintaining high accuracy
    """

    def __init__(self, api_key: str, model_name: str = 'gemini-2.0-flash-lite',
                 max_retries: int = 3, voting_rounds: int = 3):
        """
        Initialize the ExpertCrawlerAgent.

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

    def _clean_html_efficiently(self, html_content: str) -> str:
        """
        Efficiently clean HTML by removing unnecessary elements while preserving content structure.

        Args:
            html_content (str): Full HTML content

        Returns:
            str: Cleaned HTML content
        """
        if self.debug_mode:
            print("🧹 Cleaning HTML efficiently...")

        # Remove script and style tags completely
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)

        # Remove comments
        html_content = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)

        # Remove inline styles and unnecessary attributes that add noise
        html_content = re.sub(r'\s+style="[^"]*"', '', html_content)
        html_content = re.sub(r'\s+class="[^"]*"', '', html_content)
        html_content = re.sub(r'\s+id="[^"]*"', '', html_content)

        # Normalize whitespace
        html_content = re.sub(r'\s+', ' ', html_content)
        html_content = re.sub(r'>\s+<', '><', html_content)

        if self.debug_mode:
            print(f"   ✨ Cleaned HTML efficiently")

        return html_content.strip()

    def _extract_data_with_enhanced_prompt(self, html_content: str, config: Dict, round_number: int = 0) -> Any:
        """
        Extract data using enhanced prompts based on round number.

        Args:
            html_content (str): HTML content to process
            config (Dict): Configuration for extraction
            round_number (int): Current extraction round for different strategies

        Returns:
            Extracted data or None if failed
        """
        try:
            function_declaration = create_function_declaration_from_config(config)

            tools = [Tool(function_declarations=[function_declaration])]

            # Define system prompt for Expert Agent role
            system_prompt = """You are a Web Data Extraction Agent."""

            model = genai.GenerativeModel(
                model_name=self.model_name,
                tools=tools,
                system_instruction=system_prompt
            )


            # Different prompt strategies for each round
            if round_number == 0:
                # First round: Standard extraction with field guidance
                prompt = f"""
                Extract the {config['object_description']} from the HTML using the `{config['function_name']}` function.
                
                INSTRUCTIONS:
                - Extract ALL available information for each field
                - Use exact text from the HTML when possible
                - If a field is not found, set it to null
                - Pay special attention to numerical values (preserve formatting and units)
                - Look for complete text in guarantee/description fields
                
                HTML:
                {html_content}
                """

            elif round_number == 1:
                # Second round: Focus on completeness and accuracy
                prompt = f"""
                Carefully extract the {config['object_description']} using `{config['function_name']}`. Focus on COMPLETENESS and ACCURACY.
                
                EXTRACTION STRATEGY:
                - Scan the ENTIRE HTML content systematically
                - Look for both visible text and data attributes
                - For text fields, capture the FULL text, not abbreviated versions
                - For numerical fields, preserve original formatting and units
                - Double-check each field before finalizing
                
                HTML:
                {html_content}
                """

            else:
                # Third round: Thorough analysis with error prevention
                prompt = f"""
                Perform a THOROUGH extraction of {config['object_description']} using `{config['function_name']}`.
                
                QUALITY CHECKLIST:
                ✓ All required fields are extracted
                ✓ Text fields contain complete, untruncated information
                ✓ Numbers include proper units and formatting
                ✓ No placeholder or generic values
                ✓ Information matches what's actually in the HTML
                
                Be extremely careful and methodical. Extract exactly what you see in the HTML.
            
            HTML:
                {html_content}
                """

            response = model.generate_content(prompt)

            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        return part.function_call.args

            return None

        except Exception as e:
            if self.debug_mode:
                print(f"   ⚠️ Enhanced extraction failed: {e}")
            return None

    def _validate_field_quality(self, extracted_data: Any, config: Dict) -> Tuple[bool, float, List[str]]:
        """
        Validate extracted data quality using smart field analysis.

        Args:
            extracted_data: The extracted data to validate
            config (Dict): Configuration for validation

        Returns:
            Tuple[bool, float, List[str]]: (is_valid, confidence_score, issues)
        """
        if not extracted_data:
            return False, 0.0, ["No data extracted"]

        try:
            data_dict = proto_to_dict(extracted_data)
            if self.debug_mode:
                print(f"   🔍 Validating field quality: {data_dict}")

            # Extract the actual data - handle nested structure using config object_name
            object_name = config.get("object_name", "data")
            extracted_data = data_dict

            if object_name in data_dict:
                extracted_data = data_dict[object_name]
            elif isinstance(data_dict, dict) and len(data_dict) == 1:
                # If there's only one top-level key, use its value
                extracted_data = list(data_dict.values())[0]

            if self.debug_mode:
                print(f"   🔍 Object name from config: {object_name}")
                print(f"   🔍 Data dict keys: {list(data_dict.keys())}")
                print(f"   🔍 Extracted data: {extracted_data}")
                print(f"   🔍 Extracted data type: {type(extracted_data)}")
                if isinstance(extracted_data, dict):
                    print(f"   🔍 Extracted data keys: {list(extracted_data.keys())}")

            issues = []
            total_fields = len(config["fields"])
            valid_fields = 0
            quality_score = 0.0

            for field_name, field_config in config["fields"].items():
                field_value = extracted_data.get(field_name) if isinstance(extracted_data, dict) else None
                field_score = 0.0

                # Check if required field is present
                if field_config.get("required", False) and not field_value:
                    issues.append(f"Required field '{field_name}' is missing")
                    continue

                if field_value is not None:
                    valid_fields += 1

                    # Field-specific validation
                    field_type = field_config.get("type", "string")

                    if field_type == "number":
                        if isinstance(field_value, (int, float)):
                            field_score = 1.0
                        else:
                            issues.append(f"Field '{field_name}' should be a number")
                            field_score = 0.5

                    elif field_type == "string":
                        if isinstance(field_value, str):
                            # Check for minimum content quality
                            if len(field_value.strip()) > 3:
                                field_score = 1.0
                            elif len(field_value.strip()) > 0:
                                field_score = 0.7
                                issues.append(f"Field '{field_name}' seems too short")
                            else:
                                field_score = 0.3
                                issues.append(f"Field '{field_name}' is empty or whitespace")
                        else:
                            issues.append(f"Field '{field_name}' should be a string")
                            field_score = 0.5

                    # Check for common extraction errors
                    if isinstance(field_value, str):
                        # Detect placeholder or error text
                        error_indicators = ['null', 'undefined', 'not found', 'n/a', 'no data', 'error']
                        if any(indicator in field_value.lower() for indicator in error_indicators):
                            issues.append(f"Field '{field_name}' contains error text: {field_value}")
                            field_score *= 0.3

                quality_score += field_score

            # Calculate overall confidence
            if total_fields > 0:
                confidence = quality_score / total_fields
                is_valid = confidence >= 0.6 and len(issues) <= 2
            else:
                confidence = 0.0
                is_valid = False

                if self.debug_mode:
                    print(f"   📊 Quality score: {confidence:.2f}, Valid fields: {valid_fields}/{total_fields}")
                if issues:
                    print(f"   ⚠️ Issues found: {'; '.join(issues[:3])}")

            return is_valid, confidence, issues

        except Exception as e:
            if self.debug_mode:
                print(f"   ⚠️ Validation failed: {e}")
            return False, 0.0, [f"Validation error: {str(e)}"]

    def _extract_with_smart_retry(self, html_content: str, config: Dict, round_number: int = 0) -> Tuple[Any, float]:
        """
        Extract data with smart validation and retry mechanism.

        Args:
            html_content (str): HTML content to process
            config (Dict): Configuration for extraction
            round_number (int): Current round number for different strategies

        Returns:
            Tuple[Any, float]: (best_extraction, confidence_score)
        """
        if self.debug_mode:
            print(f"🎯 Smart extraction round {round_number + 1}")

        best_extraction = None
        best_confidence = 0.0

        for attempt in range(2):  # Reduced from 3 to 2 attempts per round
            if self.debug_mode:
                print(f"   🔄 Attempt {attempt + 1}/2")

            # Extract data with enhanced prompts
            extracted = self._extract_data_with_enhanced_prompt(html_content, config, round_number)

            if extracted:
                # Validate using smart field analysis
                is_valid, confidence, issues = self._validate_field_quality(extracted, config)

                if is_valid and confidence > best_confidence:
                    best_extraction = extracted
                    best_confidence = confidence

                    # If we have very high confidence, break early
                    if confidence > 0.9:
                        if self.debug_mode:
                            print(f"   ✅ Excellent extraction: {confidence:.2f}")
                        break
                elif confidence > best_confidence:
                    # Even if not valid, keep if it's better than previous attempts
                    best_extraction = extracted
                    best_confidence = confidence

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

    def _intelligent_merge(self, extractions: List[Tuple[Any, float]], config: Dict) -> Any:
        """
        Intelligently merge multiple extractions with confidence weighting.

        Args:
            extractions (List[Tuple[Any, float]]): List of (extraction, confidence) tuples
            config (Dict): Configuration containing object_name for structure

        Returns:
            Any: Best merged extraction
        """
        if self.debug_mode:
            print("🧠 Intelligent merging of extractions...")

        if not extractions:
            return None

        # Sort by confidence (highest first)
        extractions.sort(key=lambda x: x[1], reverse=True)

        # Convert all extractions to dictionaries and extract data using config object_name
        object_name = config.get("object_name", "data")
        processed_data = []
        for extraction, confidence in extractions:
            if extraction:
                try:
                    data_dict = proto_to_dict(extraction)
                    # Extract the data from nested structure using config object_name
                    if isinstance(data_dict, dict):
                        if object_name in data_dict:
                            data = data_dict[object_name]
                        elif len(data_dict) == 1:
                            # If there's only one top-level key, use its value
                            data = list(data_dict.values())[0]
                        else:
                            # Assume the whole dict is the data
                            data = data_dict
                        processed_data.append((data, confidence))
                except Exception as e:
                    if self.debug_mode:
                        print(f"   ⚠️ Failed to process extraction: {e}")
                    continue

        if not processed_data:
            return None

        # Start with the highest confidence extraction as base
        base_data = processed_data[0][0].copy()
        highest_confidence = processed_data[0][1]

        if self.debug_mode:
            print(f"   📊 Base extraction (confidence: {highest_confidence:.2f}): {base_data}")

        # Enhance with better values from other extractions
        for data, confidence in processed_data[1:]:
            for field_name, field_value in data.items():
                current_value = base_data.get(field_name)

                # Replace current value if:
                # 1. Current field is missing or null
                # 2. Current field is shorter text and new one is longer
                # 3. Current field has error indicators
                should_replace = False
                reason = ""
                if current_value is None and field_value is not None:
                    should_replace = True
                    reason = "filling missing field"
                elif isinstance(current_value, str) and isinstance(field_value, str):
                    # Check for error indicators in current value
                    error_indicators = ['null', 'undefined', 'not found', 'n/a', 'no data', 'error']
                    if any(indicator in current_value.lower() for indicator in error_indicators):
                        should_replace = True
                        reason = "replacing error text"
                    elif len(field_value.strip()) > len(current_value.strip()):
                        should_replace = True
                        reason = "using more complete text"

                if should_replace:
                    base_data[field_name] = field_value
                    if self.debug_mode:
                        print(f"   🔄 Updated {field_name}: {reason}")

        # Return the expected nested format using config object_name
        final_result = {object_name: base_data}

        if self.debug_mode:
            print(f"   ✅ Final merged result: {final_result}")

        return final_result

    def process_html(self, html_file_path: str, config_file_path: str):
        """
        Process HTML content with improved advanced techniques.

        Args:
            html_file_path (str): Path to the HTML file to process
            config_file_path (str): Path to the configuration file

        Returns:
            Structured data extracted from the HTML with high accuracy
        """
        if self.debug_mode:
            print("🚀 Starting Improved Expert HTML Processing...")
        
        # Load configuration and HTML
        with open(config_file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Step 1: Clean HTML efficiently (remove noise without losing content)
        cleaned_html = self._clean_html_efficiently(html_content)
        
        # Step 2: Multiple smart extraction rounds
        extractions_with_confidence = []
        
        for round_num in range(self.voting_rounds):
            if self.debug_mode:
                print(f"🎲 Extraction round {round_num + 1}/{self.voting_rounds}")
            
            # Use the appropriate HTML version for each round
            if round_num == 0:
                # First round: use cleaned HTML with enhanced prompts
                html_to_use = cleaned_html
            elif round_num == 1:
                # Second round: use original HTML for comparison
                html_to_use = html_content
            else:
                # Third round: use cleaned HTML with different strategy
                html_to_use = cleaned_html
            
            extraction, confidence = self._extract_with_smart_retry(html_to_use, config, round_num)
            
            if extraction and confidence > 0.3:  # Only include reasonable extractions
                extractions_with_confidence.append((extraction, confidence))
            if self.debug_mode:
                print(f"   ✅ Round {round_num + 1} completed with confidence: {confidence:.2f}")
        
        # Step 3: Intelligent merging instead of simple voting
        if extractions_with_confidence:
            final_result = self._intelligent_merge(extractions_with_confidence, config)
            avg_confidence = sum(conf for _, conf in extractions_with_confidence) / len(extractions_with_confidence)
            
            if self.debug_mode:
                print(f"🎯 Processing complete! Average confidence: {avg_confidence:.2f}")
                print(f"📊 Successful extractions: {len(extractions_with_confidence)}/{self.voting_rounds}")
            
            return final_result
        else:
            if self.debug_mode:
                print("❌ All extraction attempts failed!")
            return None
