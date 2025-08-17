#!/usr/bin/env python3
"""
LLM Judge system for evaluating agent extraction results using Google's Gemini API with Gemma 3.
Automatically validates extracted fields against original HTML content.
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, Optional
import google.generativeai as genai
from bs4 import BeautifulSoup

from dotenv import load_dotenv


class GemmaLLMJudge:
    """LLM Judge using Google's Gemini API with free Gemma 3 model."""
    
    def __init__(self, model_name: str = "gemma-3-27b-it", config_file: str = "configs/single_project_config.json"):
        """
        Initialize LLM Judge with Google Gemini API.
        
        Args:
            model_name: Name of the Gemma model to use
                       Options: gemma-2-2b-it, gemma-2-9b-it, gemma-2-27b-it
            config_file: Path to the configuration file with field descriptions
        """
        self.model_name = model_name
        
        # Load field descriptions from config
        self.field_config = self._load_field_config(config_file)
        
        # Configure Gemini API
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        
        # Initialize the model
        try:
            self.model = genai.GenerativeModel(model_name)
            print(f"✅ Successfully initialized Gemini API with model: {model_name}")
            print(f"✅ Loaded field descriptions for {len(self.field_config.get('fields', {}))} fields")
        except Exception as e:
            print(f"❌ Error initializing Gemini model: {e}")
            print("💡 Available models: gemma-2-2b-it, gemma-2-9b-it, gemma-2-27b-it")
            raise
    
    def _load_field_config(self, config_file: str) -> Dict:
        """Load field descriptions from the configuration file."""
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config
            else:
                print(f"⚠️ Config file not found: {config_file}, using defaults")
                return {}
        except Exception as e:
            print(f"⚠️ Error loading config file: {e}, using defaults")
            return {}
    
    def _get_field_context_string(self, field_name: str) -> str:
        """Generate field context string for a specific field from config."""
        fields = self.field_config.get("fields", {})
        
        if field_name not in fields:
            return f"Field: {field_name} (no specific description available)"
        
        field_info = fields[field_name]
        description = field_info.get("description", "No description")
        field_type = field_info.get("type", "unknown")
        required = field_info.get("required", False)
        
        context = f"Field: {field_name} - {description}"
        if field_type:
            context += f" (type: {field_type})"
        if required:
            context += " [required]"
        
        return context
    
    def _call_llm(self, prompt: str, max_tokens: int = 1000) -> str:
        """
        Call the Gemma model via Google Gemini API.
        
        Args:
            prompt: Input prompt for the model
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response text
        """
        try:
            # Configure generation parameters
            generation_config = genai.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=0.1,  # Low temperature for consistent evaluation
                top_p=0.9,
                top_k=40
            )
            
            # Generate response
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            return response.text.strip() if response.text else ""
            
        except Exception as e:
            print(f"❌ Error calling Gemini API: {e}")
            # Rate limiting or quota exceeded
            if "quota" in str(e).lower() or "rate" in str(e).lower():
                print("💡 API quota exceeded. Waiting 60 seconds...")
                time.sleep(60)
                return ""
            return ""
    
    def clean_html_content(self, html_content: str) -> str:
        """Extract and clean text content from HTML."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "noscript"]):
                script.decompose()
            
            # Get text and clean it
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Limit length to avoid token limits (Gemini free tier has limits)
            if len(text) > 3000:
                text = text[:3000] + "..."
            
            return text
            
        except Exception as e:
            print(f"❌ Error cleaning HTML: {e}")
            return html_content[:3000]
    
    def evaluate_field_all_agents(self, field_name: str, basic_value: any, function_value: any, 
                                 expert_value: any, html_content: str, project_context: str = "") -> Dict:
        """
        Evaluate all three agents' extractions for a single field simultaneously.
        Optimizes by grouping identical responses to reduce API calls.
        
        Args:
            field_name: Name of the field being evaluated
            basic_value: Value extracted by basic agent
            function_value: Value extracted by function agent
            expert_value: Value extracted by expert agent
            html_content: Original HTML content
            project_context: Additional context about the project
            
        Returns:
            Dictionary with evaluation results for all three agents
        """
        
        # Clean HTML content
        clean_html = self.clean_html_content(html_content)
        
        # Format extracted values for display
        def format_value(value):
            if value is None:
                return "NULL/NOT_FOUND"
            elif isinstance(value, str) and len(value.strip()) == 0:
                return "EMPTY_STRING"
            else:
                return str(value)
        
        # Normalize values for comparison (handle None vs empty string consistently)
        def normalize_value(value):
            if value is None or (isinstance(value, str) and value.strip() == ""):
                return None
            elif isinstance(value, str):
                return value.strip()
            else:
                return str(value).strip()
        
        basic_display = format_value(basic_value)
        function_display = format_value(function_value)
        expert_display = format_value(expert_value)
        
        basic_normalized = normalize_value(basic_value)
        function_normalized = normalize_value(function_value)
        expert_normalized = normalize_value(expert_value)
        
        # Group agents by identical responses
        value_groups = {}
        agent_mapping = {
            1: ("basic", basic_normalized, basic_display),
            2: ("function", function_normalized, function_display),
            3: ("expert", expert_normalized, expert_display)
        }
        
        # Create groups of agents with identical values
        for agent_num, (agent_name, normalized_val, display_val) in agent_mapping.items():
            value_key = str(normalized_val) if normalized_val is not None else "NULL"
            if value_key not in value_groups:
                value_groups[value_key] = {
                    "agents": [],
                    "display_value": display_val,
                    "normalized_value": normalized_val
                }
            value_groups[value_key]["agents"].append(agent_num)
        
        print(f"    📊 Found {len(value_groups)} unique response(s) for field '{field_name}'")
        
        # If all three agents have identical responses, evaluate once
        if len(value_groups) == 1:
            return self._evaluate_identical_responses(field_name, value_groups, clean_html)
        
        # If we have 2-3 different groups, use the optimized multi-group evaluation
        return self._evaluate_grouped_responses(field_name, value_groups, clean_html)
    
    def _evaluate_identical_responses(self, field_name: str, value_groups: Dict, clean_html: str) -> Dict:
        """
        Evaluate when all three agents have identical responses.
        Only makes one API call to evaluate the shared response.
        """
        # Get the single group (all agents have same response)
        group = list(value_groups.values())[0]
        agents = group["agents"]
        display_value = group["display_value"]
        
        print(f"    🎯 All agents identical - evaluating once: '{display_value}'")
        
        # Get field context from config for this specific field
        field_context = self._get_field_context_string(field_name)
        
        # Create single evaluation prompt
        prompt = f"""You are an expert data extraction evaluator. Your task is to determine if an extracted value is correct based on the source HTML content.
 
 Field Name: {field_name}
 Extracted Value: {display_value}
 
 Source HTML Content (cleaned):
 {clean_html}
 
 Context: This is a crowdfunding project page in Persian/Farsi language.
 {field_context}

Your evaluation should consider:
1. Is the extracted value present in the HTML content?
2. Is it the correct value for this field type?
3. Is the extraction accurate and complete?
4. Are there any obvious errors or mismatches?

Please respond in this exact format:
DECISION: [CORRECT/INCORRECT]
CONFIDENCE: [0.0-1.0]
EXPLANATION: [Brief explanation of your decision]

Important: Be strict in your evaluation. Only mark as CORRECT if you are confident the extraction is accurate."""

        try:
            response = self._call_llm(prompt, max_tokens=500)
            
            # Parse LLM response
            is_correct = False
            confidence = 0.5
            explanation = "Failed to parse LLM response"
            
            if response:
                lines = response.strip().split('\n')
                for line in lines:
                    if line.startswith('DECISION:'):
                        decision = line.split(':', 1)[1].strip().upper()
                        is_correct = decision == 'CORRECT'
                    elif line.startswith('CONFIDENCE:'):
                        try:
                            confidence = float(line.split(':', 1)[1].strip())
                            confidence = max(0.0, min(1.0, confidence))
                        except:
                            confidence = 0.5
                    elif line.startswith('EXPLANATION:'):
                        explanation = line.split(':', 1)[1].strip()
            
            # Apply the same result to all agents since they had identical responses
            correct_agents = agents if is_correct else []
            
            results = {
                "basic_correct": 1 in correct_agents,
                "function_correct": 2 in correct_agents,
                "expert_correct": 3 in correct_agents,
                "basic_explanation": explanation,
                "function_explanation": explanation,
                "expert_explanation": explanation,
                "basic_confidence": confidence,
                "function_confidence": confidence,
                "expert_confidence": confidence,
                "batch_evaluation": True,
                "identical_responses": True,
                "correct_agents": correct_agents
            }
            
            return results
            
        except Exception as e:
            error_msg = f"Error during identical response evaluation: {e}"
            return {
                "basic_correct": False,
                "function_correct": False,
                "expert_correct": False,
                "basic_explanation": error_msg,
                "function_explanation": error_msg,
                "expert_explanation": error_msg,
                "basic_confidence": 0.0,
                "function_confidence": 0.0,
                "expert_confidence": 0.0,
                "batch_evaluation": True,
                "identical_responses": True,
                "correct_agents": []
            }
    
    def _evaluate_grouped_responses(self, field_name: str, value_groups: Dict, clean_html: str) -> Dict:
        """
        Evaluate when agents have 2-3 different responses.
        Groups identical responses to minimize redundant evaluation.
        """
        group_list = list(value_groups.items())
        print(f"    🔀 Evaluating {len(group_list)} different response groups")
        
        # Create grouped evaluation prompt
        group_descriptions = []
        for i, (value_key, group_info) in enumerate(group_list, 1):
            agents_str = ", ".join([f"Agent {num}" for num in group_info["agents"]])
            group_descriptions.append(f"Group {i} ({agents_str}): {group_info['display_value']}")
        
        # Get field context from config for this specific field
        field_context = self._get_field_context_string(field_name)
        
        prompt = f"""You are an expert data extraction evaluator. Your task is to evaluate different groups of agents that extracted the same values and determine which groups are correct based on the source HTML content.
 
 Field Name: {field_name}
 
 Response Groups:
 {chr(10).join(group_descriptions)}
 
 Note: Agents within each group gave identical responses.
 
 Source HTML Content (cleaned):
 {clean_html}
 
 Context: This is a crowdfunding project page in Persian/Farsi language.
 {field_context}

Your evaluation should consider:
1. Are the extracted values present in the HTML content?
2. Are they the correct values for this field type?
3. Are the extractions accurate and complete?
4. Are there any obvious errors or mismatches?

Prefer the number values that have units instead of ones that do not.

Please respond in this exact format:
CORRECT_GROUPS: [comma-separated list of group numbers that are correct, or "none" if all incorrect]
CONFIDENCE: [0.0-1.0]
EXPLANATION: [Brief explanation of your decisions for each group]

Examples:
- If groups 1 and 3 are correct: "CORRECT_GROUPS: 1,3"
- If only group 2 is correct: "CORRECT_GROUPS: 2"
- If all groups are correct: "CORRECT_GROUPS: 1,2,3"
- If none are correct: "CORRECT_GROUPS: none"

Important: Be strict in your evaluation. Only mark as CORRECT if you are confident the extraction is accurate."""

        try:
            response = self._call_llm(prompt, max_tokens=700)
            
            # Parse LLM response
            correct_groups = []
            confidence = 0.5
            explanation = "Failed to parse LLM response"
            
            if response:
                lines = response.strip().split('\n')
                for line in lines:
                    if line.startswith('CORRECT_GROUPS:'):
                        groups_str = line.split(':', 1)[1].strip().lower()
                        if groups_str == "none":
                            correct_groups = []
                        else:
                            try:
                                group_nums = [int(x.strip()) for x in groups_str.split(',') if x.strip()]
                                correct_groups = [num for num in group_nums if 1 <= num <= len(group_list)]
                            except:
                                correct_groups = []
                    elif line.startswith('CONFIDENCE:'):
                        try:
                            confidence = float(line.split(':', 1)[1].strip())
                            confidence = max(0.0, min(1.0, confidence))
                        except:
                            confidence = 0.5
                    elif line.startswith('EXPLANATION:'):
                        explanation = line.split(':', 1)[1].strip()
            
            # Convert group results back to individual agent results
            correct_agents = []
            for group_num in correct_groups:
                if 1 <= group_num <= len(group_list):
                    group_key = list(value_groups.keys())[group_num - 1]
                    correct_agents.extend(value_groups[group_key]["agents"])
            
            results = {
                "basic_correct": 1 in correct_agents,
                "function_correct": 2 in correct_agents,
                "expert_correct": 3 in correct_agents,
                "basic_explanation": explanation,
                "function_explanation": explanation,
                "expert_explanation": explanation,
                "basic_confidence": confidence,
                "function_confidence": confidence,
                "expert_confidence": confidence,
                "batch_evaluation": True,
                "grouped_evaluation": True,
                "correct_agents": correct_agents,
                "response_groups": len(group_list)
            }
            
            return results
            
        except Exception as e:
            error_msg = f"Error during grouped evaluation: {e}"
            return {
                "basic_correct": False,
                "function_correct": False,
                "expert_correct": False,
                "basic_explanation": error_msg,
                "function_explanation": error_msg,
                "expert_explanation": error_msg,
                "basic_confidence": 0.0,
                "function_confidence": 0.0,
                "expert_confidence": 0.0,
                "batch_evaluation": True,
                "grouped_evaluation": True,
                "correct_agents": []
            }
    
    def evaluate_project(self, project_name: str) -> Optional[Dict]:
        """
        Evaluate all three agents' results for a project.
        
        Args:
            project_name: Name of the project to evaluate
            
        Returns:
            Dictionary with evaluation results or None if failed
        """
        print(f"\n🔍 LLM Evaluating project: {project_name}")
        
        # Load HTML content
        html_file = f"single_samples/{project_name}.html"
        if not os.path.exists(html_file):
            print(f"❌ HTML file not found: {html_file}")
            return None
        
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
        except Exception as e:
            print(f"❌ Error reading HTML file: {e}")
            return None
        
        # Load agent results
        agents = ["basic", "function", "expert"]
        agent_data = {}
        
        for agent in agents:
            result_file = f"results/{agent}/{project_name}_{agent}.json"
            if os.path.exists(result_file):
                try:
                    with open(result_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Extract project fields
                        if isinstance(data, dict) and "project" in data:
                            agent_data[agent] = data["project"]
                        else:
                            agent_data[agent] = data
                except Exception as e:
                    print(f"❌ Error loading {agent} results: {e}")
                    agent_data[agent] = {}
            else:
                print(f"⚠️ No results found for {agent} agent")
                agent_data[agent] = {}
        
        if not any(agent_data.values()):
            print(f"❌ No agent data found for project {project_name}")
            return None
        
        # Get all unique fields
        all_fields = set()
        for data in agent_data.values():
            if isinstance(data, dict):
                all_fields.update(data.keys())
        
        if not all_fields:
            print(f"❌ No fields found to evaluate")
            return None
        
        print(f"📊 Evaluating {len(all_fields)} fields across {len([a for a in agents if agent_data.get(a)])} agents")
        
        # Evaluation results
        evaluation_results = {
            "project_name": project_name,
            "evaluation_date": datetime.now().isoformat(),
            "llm_model": self.model_name,
            "basic_agent": {"correct": 0, "incorrect": 0, "total_confidence": 0.0},
            "function_agent": {"correct": 0, "incorrect": 0, "total_confidence": 0.0},
            "expert_agent": {"correct": 0, "incorrect": 0, "total_confidence": 0.0},
            "field_evaluations": {}
        }
        
        # Evaluate each field (batch evaluation for all agents at once)
        for field_name in sorted(all_fields):
            print(f"  📋 Evaluating field: {field_name}")
            
            # Get values for all three agents
            basic_value = agent_data.get("basic", {}).get(field_name)
            function_value = agent_data.get("function", {}).get(field_name)
            expert_value = agent_data.get("expert", {}).get(field_name)
            
            field_results = {
                "basic_value": basic_value,
                "function_value": function_value,
                "expert_value": expert_value,
                "evaluations": {}
            }
            
            # Add delay to respect API rate limits (only one call per field now)
            time.sleep(1)
            
            # Batch evaluate all three agents for this field
            batch_results = self.evaluate_field_all_agents(
                field_name, basic_value, function_value, expert_value, html_content, project_name
            )
            
            # Store batch evaluation results
            field_results["evaluations"] = batch_results
            
            # Update agent statistics
            agents_info = [
                ("basic", "basic_agent"),
                ("function", "function_agent"), 
                ("expert", "expert_agent")
            ]
            
            for agent, agent_key in agents_info:
                is_correct = batch_results[f"{agent}_correct"]
                confidence = batch_results[f"{agent}_confidence"]
                
                # Update agent stats
                if is_correct:
                    evaluation_results[agent_key]["correct"] += 1
                else:
                    evaluation_results[agent_key]["incorrect"] += 1
                
                evaluation_results[agent_key]["total_confidence"] += confidence
                
                print(f"    {agent}: {'✅' if is_correct else '❌'} (conf: {confidence:.2f})")
            
            # Show optimization details and results
            if batch_results.get("identical_responses"):
                print(f"    🎯 Optimization: All agents identical → 1 API call instead of 3")
            elif batch_results.get("grouped_evaluation"):
                groups = batch_results.get("response_groups", 0)
                print(f"    🔀 Optimization: {groups} unique responses → 1 API call instead of 3")
            
            # Show which agents were marked correct
            correct_agents = batch_results.get("correct_agents", [])
            if correct_agents:
                agent_names = {1: "Basic", 2: "Function", 3: "Expert"}
                correct_names = [agent_names[i] for i in correct_agents if i in agent_names]
                print(f"    ✅ Result: {', '.join(correct_names)} correct")
            else:
                print(f"    ❌ Result: All incorrect")
            
            evaluation_results["field_evaluations"][field_name] = field_results
        
        # Calculate average confidence for each agent
        for agent in agents:
            agent_key = f"{agent}_agent"
            total_fields = evaluation_results[agent_key]["correct"] + evaluation_results[agent_key]["incorrect"]
            if total_fields > 0:
                avg_confidence = evaluation_results[agent_key]["total_confidence"] / total_fields
                evaluation_results[agent_key]["average_confidence"] = round(avg_confidence, 3)
            else:
                evaluation_results[agent_key]["average_confidence"] = 0.0
        
        return evaluation_results


def create_llm_validation_directory():
    """Create LLM validation directory if it doesn't exist."""
    llm_validation_dir = "results/llm_validation"
    if not os.path.exists(llm_validation_dir):
        os.makedirs(llm_validation_dir)
        print(f"Created directory: {llm_validation_dir}")
    return llm_validation_dir


def save_llm_evaluation_results(evaluation_results: Dict):
    """Save LLM evaluation results to file."""
    if not evaluation_results:
        return
    
    llm_validation_dir = create_llm_validation_directory()
    project_name = evaluation_results["project_name"]
    filename = f"{project_name}_llm_validation.json"
    filepath = os.path.join(llm_validation_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(evaluation_results, f, indent=2, ensure_ascii=False)
    
    print(f"💾 LLM evaluation results saved to: {filepath}")


def print_llm_evaluation_summary(evaluation_results: Dict):
    """Print a summary of LLM evaluation results."""
    if not evaluation_results:
        return
    
    print(f"\n{'=' * 60}")
    print("🤖 LLM EVALUATION SUMMARY")
    print(f"{'=' * 60}")
    
    agents = ["basic_agent", "function_agent", "expert_agent"]
    agent_names = ["Basic Agent", "Function Agent", "Expert Agent"]
    
    for agent_key, agent_name in zip(agents, agent_names):
        if agent_key in evaluation_results:
            stats = evaluation_results[agent_key]
            total = stats["correct"] + stats["incorrect"]
            
            if total > 0:
                accuracy = (stats["correct"] / total) * 100
                avg_conf = stats.get("average_confidence", 0.0)
                
                print(f"\n🤖 {agent_name}:")
                print(f"   ✅ Correct: {stats['correct']}")
                print(f"   ❌ Incorrect: {stats['incorrect']}")
                print(f"   📊 Accuracy: {accuracy:.1f}% ({stats['correct']}/{total})")
                print(f"   🎯 Avg Confidence: {avg_conf:.3f}")
            else:
                print(f"\n🤖 {agent_name}: No evaluations")


def evaluate_all_projects_llm():
    """Evaluate all projects using LLM judge."""
    print("🚀 Starting LLM Batch Evaluation for All Projects")
    print("=" * 60)
    
    # Initialize LLM Judge
    try:
        judge = GemmaLLMJudge()
        print(f"✅ LLM Judge initialized with model: {judge.model_name}")
    except Exception as e:
        print(f"❌ Failed to initialize LLM Judge: {e}")
        return
    
    # Get all projects that have agent results
    project_names = []
    for agent in ["basic", "function", "expert"]:
        agent_dir = f"results/{agent}"
        if os.path.exists(agent_dir):
            for filename in os.listdir(agent_dir):
                if filename.endswith(f'_{agent}.json'):
                    project_name = filename[:-len(f'_{agent}.json')]
                    if project_name not in project_names:
                        project_names.append(project_name)
    
    if not project_names:
        print("❌ No agent result files found")
        return
    
    project_names.sort()
    print(f"📁 Found {len(project_names)} projects with agent results:")
    for i, project_name in enumerate(project_names, 1):
        print(f"   {i}. {project_name}")
    
    # Check which projects already have LLM evaluations
    llm_validation_dir = "results/llm_validation"
    existing_evaluations = []
    pending_evaluations = []
    
    for project_name in project_names:
        evaluation_file = os.path.join(llm_validation_dir, f"{project_name}_llm_validation.json")
        if os.path.exists(evaluation_file):
            existing_evaluations.append(project_name)
        else:
            pending_evaluations.append(project_name)
    
    if existing_evaluations:
        print(f"\n✅ Projects with existing LLM evaluations ({len(existing_evaluations)}):")
        for project_name in existing_evaluations:
            print(f"   • {project_name}")
    
    if not pending_evaluations:
        print(f"\n🎉 All projects already evaluated by LLM!")
        return
    
    print(f"\n⏳ Projects pending LLM evaluation ({len(pending_evaluations)}):")
    for i, project_name in enumerate(pending_evaluations, 1):
        print(f"   {i}. {project_name}")
    
    proceed = input(f"\n🤔 Proceed with LLM evaluation of {len(pending_evaluations)} projects? (y/n): ").lower().strip()
    if proceed not in ['y', 'yes']:
        print("❌ LLM evaluation cancelled.")
        return
    
    print(f"\n⏱️ Starting LLM evaluation...")
    
    # Track overall results
    completed_evaluations = 0
    failed_evaluations = 0
    
    # Process each pending project
    for i, project_name in enumerate(pending_evaluations, 1):
        print(f"\n{'🔄' * 60}")
        print(f"📋 LLM Evaluating Project {i}/{len(pending_evaluations)}: {project_name}")
        print(f"{'🔄' * 60}")
        
        try:
            # Run LLM evaluation for this project
            evaluation_results = judge.evaluate_project(project_name)
            
            if evaluation_results:
                save_llm_evaluation_results(evaluation_results)
                print_llm_evaluation_summary(evaluation_results)
                completed_evaluations += 1
                print(f"✅ LLM evaluation completed for {project_name}")
            else:
                failed_evaluations += 1
                print(f"❌ LLM evaluation failed for {project_name}")
            
        except KeyboardInterrupt:
            print(f"\n\n⏹️ LLM evaluation interrupted by user.")
            print(f"📊 Progress so far:")
            print(f"   ✅ Completed: {completed_evaluations}")
            print(f"   ❌ Failed: {failed_evaluations}")
            print(f"   ⏭️ Remaining: {len(pending_evaluations) - i}")
            return
            
        except Exception as e:
            print(f"❌ Error during LLM evaluation of {project_name}: {e}")
            failed_evaluations += 1
        
        # Progress indicator
        remaining = len(pending_evaluations) - i
        if remaining > 0:
            print(f"\n⏳ {remaining} projects remaining...")
    
    # Final summary
    print(f"\n{'🏁' * 60}")
    print("📊 LLM EVALUATION COMPLETE")
    print(f"{'🏁' * 60}")
    
    print(f"✅ Completed evaluations: {completed_evaluations}")
    print(f"❌ Failed evaluations: {failed_evaluations}")
    print(f"📈 Total projects processed: {len(pending_evaluations)}")
    
    if completed_evaluations > 0:
        print(f"\n💾 LLM evaluation files saved in: {llm_validation_dir}")
        print(f"🔄 Run LLM scoring next: python calculate_scores.py --llm")


if __name__ == "__main__":
    evaluate_all_projects_llm()
