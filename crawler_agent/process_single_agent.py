#!/usr/bin/env python3
"""
Process all single samples for a specific agent and update comparison files.
This script allows you to run just one agent on all projects and update existing comparisons.
"""

import os
import json
import time
from typing import Any
from dotenv import load_dotenv
from crawler_agent.agents.basic import BasicAgent
from crawler_agent.agents.function import FunctionAgent
from crawler_agent.agents.expert import ExpertAgent
from crawler_agent.agents.feedback import FeedbackAgent


def create_results_directory(agent_name: str):
    """Create results directory for the specific agent."""
    directories = [
        "results",
        f"results/{agent_name.lower()}",
        "results/comparison"
    ]

    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")


def test_single_agent(agent, agent_name: str, input_file: str, config_file: str, output_file: str):
    """Test a single agent and return results."""
    print(f"\n{'=' * 50}")
    print(f"🧪 Testing {agent_name}")
    print(f"{'=' * 50}")

    start_time = time.time()

    try:
        # Always process (overwrite existing files)
        agent.process_and_save(input_file, config_file, output_file)

        end_time = time.time()
        processing_time = end_time - start_time

        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)

            print(f"✅ {agent_name} completed in {processing_time:.2f} seconds")
            return {
                "agent_name": agent_name,
                "success": True,
                "processing_time": processing_time,
                "data": saved_data,
                "error": None
            }
        else:
            print(f"❌ {agent_name} failed - no output file created")
            return {
                "agent_name": agent_name,
                "success": False,
                "processing_time": processing_time,
                "data": None,
                "error": "No output file created"
            }

    except Exception as e:
        end_time = time.time()
        processing_time = end_time - start_time
        print(f"❌ {agent_name} failed after {processing_time:.2f} seconds: {e}")
        return {
            "agent_name": agent_name,
            "success": False,
            "processing_time": processing_time,
            "data": None,
            "error": str(e)
        }


def update_comparison_file(project_name: str, agent_name: str, agent_result: dict):
    """Update or create comparison file with the new agent result."""
    comparison_file = f"results/comparison/{project_name}_comparison.json"

    # Load existing comparison data or create new
    if os.path.exists(comparison_file):
        with open(comparison_file, 'r', encoding='utf-8') as f:
            comparison_data = json.load(f)
    else:
        comparison_data = {
            "basic_agent": None,
            "function_agent": None,
            "expert_agent": None,
            "feedback_agent": None,
            "summary": {
                "successful_count": 0,
                "total_count": 3,
                "fastest_agent": None
            }
        }

    # Update the specific agent's data
    agent_key = f"{agent_name.lower()}_agent"
    comparison_data[agent_key] = agent_result

    # Recalculate summary
    agents = ["basic_agent", "function_agent", "expert_agent", "feedback_agent"]
    successful_agents = []

    for agent_key in agents:
        if comparison_data[agent_key] and comparison_data[agent_key]["success"]:
            successful_agents.append(comparison_data[agent_key])

    comparison_data["summary"]["successful_count"] = len(successful_agents)

    # Find fastest agent
    if successful_agents:
        fastest = min(successful_agents, key=lambda x: x["processing_time"])
        comparison_data["summary"]["fastest_agent"] = fastest["agent_name"]
    else:
        comparison_data["summary"]["fastest_agent"] = None

    # Save updated comparison
    with open(comparison_file, 'w', encoding='utf-8') as f:
        json.dump(comparison_data, f, indent=2, ensure_ascii=False)

    print(f"📊 Updated comparison file: {comparison_file}")


def process_agent_for_all_projects(agent_name: str, agent_instance: Any,
                                   config_file: str = "configs/single_project_config.json"):
    """
    Process all single samples for a specific agent.
    
    Args:
        agent_name (str): Name of the agent (e.g., "Basic", "Function", "Expert", "Feedback")
        agent_instance: Instance of the agent class
        config_file (str): Path to the configuration file
    """
    print(f"🚀 Starting Single Agent Processing: {agent_name}")
    print("=" * 60)

    # Validate config file
    if not os.path.exists(config_file):
        print(f"❌ Config file not found: {config_file}")
        return

    # Create results directory for this agent
    create_results_directory(agent_name)

    # Get all project names from single_samples folder
    single_samples_dir = "single_samples"
    if not os.path.exists(single_samples_dir):
        print(f"❌ Directory not found: {single_samples_dir}")
        return

    # Find all HTML files and extract project names
    project_names = []
    for filename in os.listdir(single_samples_dir):
        if filename.endswith('.html'):
            project_name = filename[:-5]  # Remove .html extension
            project_names.append(project_name)

    if not project_names:
        print(f"❌ No HTML files found in {single_samples_dir}")
        return

    project_names.sort()  # Sort alphabetically for consistent processing

    print(f"📁 Found {len(project_names)} projects:")
    for i, project_name in enumerate(project_names, 1):
        print(f"   {i}. {project_name}")

    print(f"\n⏱️ Starting processing with {agent_name} Agent...")

    # Track results
    successful_projects = 0
    failed_projects = 0
    start_time = time.time()

    # Process each project
    for i, project_name in enumerate(project_names, 1):
        print(f"\n{'🔄' * 60}")
        print(f"📋 Processing Project {i}/{len(project_names)}: {project_name}")
        print(f"{'🔄' * 60}")

        # File paths
        html_file = f"{single_samples_dir}/{project_name}.html"
        output_file = f"results/{agent_name.lower()}/{project_name}_{agent_name.lower()}.json"

        if not os.path.exists(html_file):
            print(f"❌ HTML file not found: {html_file}")
            failed_projects += 1
            continue

        if os.path.exists(output_file):
            print(f"Already calculated. Skipping project: {project_name}")
            continue

        # Test the agent
        agent_result = test_single_agent(agent_instance, f"{agent_name} Agent", html_file, config_file, output_file)

        # Update comparison file
        try:
            update_comparison_file(project_name, agent_name, agent_result)

            if agent_result["success"]:
                successful_projects += 1
            else:
                failed_projects += 1

        except Exception as e:
            print(f"❌ Failed to update comparison for {project_name}: {e}")
            failed_projects += 1

        # Progress indicator
        remaining = len(project_names) - i
        if remaining > 0:
            print(f"\n⏳ {remaining} projects remaining...")

    # Final summary
    end_time = time.time()
    total_time = end_time - start_time

    print(f"\n{'🏁' * 60}")
    print(f"📊 {agent_name.upper()} AGENT PROCESSING COMPLETE")
    print(f"{'🏁' * 60}")

    print(f"✅ Successful projects: {successful_projects}")
    print(f"❌ Failed projects: {failed_projects}")
    print(f"📈 Total projects: {len(project_names)}")
    print(f"⏱️ Total processing time: {total_time:.2f} seconds")
    print(f"⚡ Average time per project: {total_time / len(project_names):.2f} seconds")

    print(f"\n💾 Results saved to:")
    print(f"   📁 Agent results: results/{agent_name.lower()}/")
    print(f"   📊 Updated comparisons: results/comparison/")


def process_basic_agent():
    """Process all projects with Basic Agent only."""
    print("🔄 Processing with Basic Agent...")

    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")

    basic_agent = BasicAgent(api_key=api_key)
    process_agent_for_all_projects("Basic", basic_agent)


def process_function_agent():
    """Process all projects with Function Agent only."""
    print("🔄 Processing with Function Agent...")

    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")

    function_agent = FunctionAgent(api_key=api_key)
    process_agent_for_all_projects("Function", function_agent)


def process_expert_agent():
    """Process all projects with Expert Agent only."""
    print("🔄 Processing with Expert Agent...")

    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")

    expert_agent = ExpertAgent(api_key=api_key)
    process_agent_for_all_projects("Expert", expert_agent)


def process_feedback_agent():
    """Process all projects with Feedback Agent only."""
    print("🔄 Processing with Feedback Agent...")

    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")

    feedback_agent = FeedbackAgent(api_key=api_key)
    process_agent_for_all_projects("Feedback", feedback_agent)


def load_project_results(project_name):
    """Load results from all three agents for a project."""
    basic_file = f"results/basic/{project_name}_basic.json"
    function_file = f"results/function/{project_name}_function.json"
    expert_file = f"results/expert/{project_name}_expert.json"
    feedback_file = f"results/feedback/{project_name}_feedback.json"

    basic_data = None
    function_data = None
    expert_data = None
    feedback_data = None

    if os.path.exists(basic_file):
        with open(basic_file, 'r', encoding='utf-8') as f:
            basic_data = json.load(f)

    if os.path.exists(function_file):
        with open(function_file, 'r', encoding='utf-8') as f:
            function_data = json.load(f)

    if os.path.exists(expert_file):
        with open(expert_file, 'r', encoding='utf-8') as f:
            expert_data = json.load(f)

    if os.path.exists(feedback_file):
        with open(feedback_file, 'r', encoding='utf-8') as f:
            feedback_data = json.load(f)

    return basic_data, function_data, expert_data, feedback_data


def validate_single_agent_for_all_projects(agent_name: str):
    """
    Re-validate only one agent for all projects while keeping other agents' validations.
    
    Args:
        agent_name (str): Name of the agent to re-validate ("Basic", "Function", "Expert", or "Feedback")
    """
    print(f"🔍 Starting Single Agent Re-Validation: {agent_name}")
    print("=" * 60)
    
    # Import validation functions
    from validate_results import (
        create_validation_directory, 
        extract_project_fields,
        format_field_value
    )
    from datetime import datetime
    
    # Validate agent name
    valid_agents = ["Basic", "Function", "Expert", "Feedback"]
    if agent_name not in valid_agents:
        print(f"❌ Invalid agent name: {agent_name}")
        print(f"Valid options: {', '.join(valid_agents)}")
        return
    
    # Get all projects that have results for this agent
    agent_dir = f"results/{agent_name.lower()}"
    if not os.path.exists(agent_dir):
        print(f"❌ No results found for {agent_name} agent: {agent_dir}")
        print(f"💡 Run processing first: process_{agent_name.lower()}_agent()")
        return
    
    # Find all projects with results for this agent
    project_names = []
    for filename in os.listdir(agent_dir):
        if filename.endswith(f'_{agent_name.lower()}.json'):
            project_name = filename[:-len(f'_{agent_name.lower()}.json')]
            project_names.append(project_name)
    
    if not project_names:
        print(f"❌ No result files found for {agent_name} agent in {agent_dir}")
        return
    
    project_names.sort()
    
    print(f"📁 Found {len(project_names)} projects with {agent_name} agent results:")
    for i, project_name in enumerate(project_names, 1):
        print(f"   {i}. {project_name}")
    
    # Check existing validations
    validation_dir = create_validation_directory()
    projects_to_validate = []
    
    for project_name in project_names:
        validation_file = os.path.join(validation_dir, f"{project_name}_validation.json")
        if os.path.exists(validation_file):
            projects_to_validate.append((project_name, "update"))
        else:
            projects_to_validate.append((project_name, "create"))
    
    update_count = sum(1 for _, action in projects_to_validate if action == "update")
    create_count = sum(1 for _, action in projects_to_validate if action == "create")
    
    if update_count > 0:
        print(f"\n🔄 Will update existing validations: {update_count}")
    if create_count > 0:
        print(f"✨ Will create new validations: {create_count}")
    
    print(f"\n📝 Re-Validation Instructions:")
    print(f"   • You're only validating {agent_name} agent results")
    print("   • Other agents' validations will remain unchanged")
    print("   • When values are same: t=true, f=false, s=skip")
    print("   • When values differ: select correct numbers")
    print("   • You can quit anytime with Ctrl+C")
    
    proceed = input(f"\n🤔 Proceed with re-validating {agent_name} agent for {len(project_names)} projects? (y/n): ").lower().strip()
    if proceed not in ['y', 'yes']:
        print("❌ Single agent re-validation cancelled.")
        return
    
    # Track results
    completed_validations = 0
    failed_validations = 0
    
    # Process each project
    for i, (project_name, action) in enumerate(projects_to_validate, 1):
        print(f"\n{'🔄' * 60}")
        print(f"📋 Re-validating {agent_name} Agent - Project {i}/{len(project_names)}: {project_name}")
        print(f"{'🔄' * 60}")
        
        try:
            # Load existing validation or create new structure
            validation_file = os.path.join(validation_dir, f"{project_name}_validation.json")
            
            if action == "update":
                # Load existing validation
                with open(validation_file, 'r', encoding='utf-8') as f:
                    validation_results = json.load(f)
                print(f"📂 Loaded existing validation for {project_name}")
            else:
                # Create new validation structure
                validation_results = {
                    "project_name": project_name,
                    "validation_date": datetime.now().isoformat(),
                    "basic_agent": {"correct": 0, "incorrect": 0, "skipped": 0},
                    "function_agent": {"correct": 0, "incorrect": 0, "skipped": 0},
                    "expert_agent": {"correct": 0, "incorrect": 0, "skipped": 0},
                    "feedback_agent": {"correct": 0, "incorrect": 0, "skipped": 0},
                    "field_validations": {}
                }
                print(f"✨ Created new validation for {project_name}")
            
            # Load data from all three agents
            basic_data, function_data, expert_data, feedback_data = load_project_results(project_name)
            
            if not any([basic_data, function_data, expert_data, feedback_data]):
                print(f"❌ No data found for project '{project_name}'")
                failed_validations += 1
                continue
            
            # Extract project fields
            basic_fields = extract_project_fields(basic_data)
            function_fields = extract_project_fields(function_data)
            expert_fields = extract_project_fields(expert_data)
            feedback_fields = extract_project_fields(feedback_data)

            print(f"📊 Data loaded:")
            print(f"   Basic Agent: {'✅' if basic_data else '❌'} ({len(basic_fields)} fields)")
            print(f"   Function Agent: {'✅' if function_data else '❌'} ({len(function_fields)} fields)")
            print(f"   Expert Agent: {'✅' if expert_data else '❌'} ({len(expert_fields)} fields)")
            print(f"   Feedback Agent: {'✅' if feedback_data else '❌'} ({len(feedback_fields)} fields)")

            # Get all unique field names
            all_fields = set()
            all_fields.update(basic_fields.keys())
            all_fields.update(function_fields.keys())
            all_fields.update(expert_fields.keys())
            all_fields.update(feedback_fields.keys())

            if not all_fields:
                print("❌ No fields found to validate")
                failed_validations += 1
                continue
            
            # Reset only the target agent's counters
            agent_key = f"{agent_name.lower()}_agent"
            validation_results[agent_key] = {"correct": 0, "incorrect": 0, "skipped": 0}
            
            print(f"\n🎯 Re-validating {agent_name} agent for {len(all_fields)} fields...")
            
            # Build a project-specific knowledge base from existing validation
            print(f"🧠 Building project-specific validation knowledge base...")
            validation_knowledge = {}  # {normalized_value: {True: count, False: count, None: count}}
            
            # Only use validation data from the SAME project
            current_validation_file = os.path.join(validation_dir, f"{project_name}_validation.json")
            if os.path.exists(current_validation_file):
                try:
                    with open(current_validation_file, 'r', encoding='utf-8') as f:
                        existing_validation = json.load(f)
                    
                    # Extract validations from this project only
                    for field, field_data in existing_validation.get("field_validations", {}).items():
                        # Check all three agents' values and validations from THIS project
                        for agent_type in ["basic", "function", "expert", "feedback"]:
                            value = field_data.get(f"{agent_type}_value")
                            validation = field_data.get(f"{agent_type}_correct")
                            
                            if value is not None and validation is not None:
                                # Normalize value for comparison
                                normalized_value = str(value).strip() if value is not None else "NULL"
                                
                                if normalized_value not in validation_knowledge:
                                    validation_knowledge[normalized_value] = {True: 0, False: 0, None: 0}
                                
                                validation_knowledge[normalized_value][validation] += 1
                
                except Exception as e:
                    print(f"⚠️ Warning: Could not read validation file {current_validation_file}: {e}")
            
            # Show knowledge base summary
            known_values = len(validation_knowledge)
            if known_values > 0:
                print(f"🧠 Project-specific knowledge base built: {known_values} unique values from {project_name}")
            else:
                print(f"🧠 No previous validation data found for {project_name} - all validations will be manual")
            
            # Validate each field (only update the target agent)
            auto_validated = 0
            manual_validations = 0
            
            for field_name in sorted(all_fields):
                basic_value = basic_fields.get(field_name)
                function_value = function_fields.get(field_name)
                expert_value = expert_fields.get(field_name)
                feedback_value = feedback_fields.get(field_name)

                # Get current field validation or create new
                if field_name not in validation_results["field_validations"]:
                    validation_results["field_validations"][field_name] = {
                        "basic_value": basic_value,
                        "function_value": function_value,
                        "expert_value": expert_value,
                        "feedback_value": feedback_value,
                        "basic_correct": None,
                        "function_correct": None,
                        "expert_correct": None,
                        "feedback_correct": None
                    }
                else:
                    # Update values (they might have changed)
                    validation_results["field_validations"][field_name]["basic_value"] = basic_value
                    validation_results["field_validations"][field_name]["function_value"] = function_value
                    validation_results["field_validations"][field_name]["expert_value"] = expert_value
                    validation_results["field_validations"][field_name]["feedback_value"] = feedback_value

                # Get target value
                target_value = None
                if agent_name == "Basic":
                    target_value = basic_value
                elif agent_name == "Function":
                    target_value = function_value
                elif agent_name == "Expert":
                    target_value = expert_value
                elif agent_name == "Feedback":
                    target_value = feedback_value
                
                # Normalize target value for knowledge lookup
                normalized_target = str(target_value).strip() if target_value is not None else "NULL"
                
                # Check if we have previous knowledge about this value
                result = None
                auto_validated_reason = None
                
                if normalized_target in validation_knowledge:
                    knowledge = validation_knowledge[normalized_target]
                    
                    # Use the most common validation result for this value
                    if knowledge[True] > knowledge[False] and knowledge[True] > knowledge[None]:
                        result = True
                        auto_validated_reason = f"Previously validated as CORRECT {knowledge[True]} times"
                    elif knowledge[False] > knowledge[True] and knowledge[False] > knowledge[None]:
                        result = False
                        auto_validated_reason = f"Previously validated as INCORRECT {knowledge[False]} times"
                    elif knowledge[None] > knowledge[True] and knowledge[None] > knowledge[False]:
                        result = None
                        auto_validated_reason = f"Previously SKIPPED {knowledge[None]} times"
                    
                    # If there's a clear majority (more than 50%), use auto-validation
                    total_validations = sum(knowledge.values())
                    if result is not None and knowledge[result] / total_validations > 0.5:
                        # Auto-validate based on previous knowledge
                        target_display = format_field_value(target_value)
                        
                        print(f"\n📋 Field: {field_name}")
                        print(f"🧠 Auto-validated: {target_display}")
                        print(f"💡 Reason: {auto_validated_reason}")
                        
                        auto_validated += 1
                    else:
                        # Conflicting previous validations, ask user
                        result = None
                        auto_validated_reason = None
                
                # If no auto-validation possible, ask user
                if result is None or auto_validated_reason is None:
                    # Show current validation status for other agents
                    field_validation = validation_results["field_validations"][field_name]
                    other_validations = []
                    if agent_name != "Basic" and field_validation.get("basic_correct") is not None:
                        status = "✅" if field_validation["basic_correct"] else "❌"
                        other_validations.append(f"Basic: {status}")
                    if agent_name != "Function" and field_validation.get("function_correct") is not None:
                        status = "✅" if field_validation["function_correct"] else "❌"
                        other_validations.append(f"Function: {status}")
                    if agent_name != "Expert" and field_validation.get("expert_correct") is not None:
                        status = "✅" if field_validation["expert_correct"] else "❌"
                        other_validations.append(f"Expert: {status}")
                    if agent_name != "Feedback" and field_validation.get("feedback_correct") is not None:
                        status = "✅" if field_validation["feedback_correct"] else "❌"
                        other_validations.append(f"Feedback: {status}")
                    
                    print(f"\n📋 Field: {field_name}")
                    if other_validations:
                        print(f"🔒 Other agents: {', '.join(other_validations)}")
                    
                    target_display = format_field_value(target_value)
                    print(f"🎯 {agent_name} Agent: {target_display}")
                    
                    # Show knowledge hint if available
                    if normalized_target in validation_knowledge:
                        knowledge = validation_knowledge[normalized_target]
                        print(f"💡 Previous validations: ✅{knowledge[True]} ❌{knowledge[False]} ⏭️{knowledge[None]}")
                    
                    # Get validation for just this agent
                    while True:
                        user_input = input("✅ Is this correct? (t=true/f=false/s=skip): ").lower().strip()
                        if user_input in ['t', 'true']:
                            result = True
                            break
                        elif user_input in ['f', 'false']:
                            result = False
                            break
                        elif user_input in ['s', 'skip']:
                            result = None
                            break
                        else:
                            print("❌ Invalid input. Please use 't', 'f', or 's'.")
                    
                    manual_validations += 1
                
                # Update only the target agent's validation
                if agent_name == "Basic":
                    validation_results["field_validations"][field_name]["basic_correct"] = result
                elif agent_name == "Function":
                    validation_results["field_validations"][field_name]["function_correct"] = result
                elif agent_name == "Expert":
                    validation_results["field_validations"][field_name]["expert_correct"] = result
                elif agent_name == "Feedback":
                    validation_results["field_validations"][field_name]["feedback_correct"] = result
                
                # Update counters
                if result is True:
                    validation_results[agent_key]["correct"] += 1
                elif result is False:
                    validation_results[agent_key]["incorrect"] += 1
                else:  # None (skipped)
                    validation_results[agent_key]["skipped"] += 1
            
            print(f"\n📊 Validation Summary:")
            print(f"   🧠 Auto-validated: {auto_validated}")
            print(f"   👤 Manual validations: {manual_validations}")
            print(f"   📈 Total fields: {len(all_fields)}")
            
            # Update validation date
            validation_results["validation_date"] = datetime.now().isoformat()
            
            # Save updated validation
            with open(validation_file, 'w', encoding='utf-8') as f:
                json.dump(validation_results, f, indent=2, ensure_ascii=False)
            
            completed_validations += 1
            print(f"✅ Re-validation completed for {project_name}")
            
            # Show agent summary
            stats = validation_results[agent_key]
            evaluated = stats["correct"] + stats["incorrect"]
            if evaluated > 0:
                accuracy = (stats["correct"] / evaluated) * 100
                print(f"📊 {agent_name} Agent: {accuracy:.1f}% accuracy ({stats['correct']}/{evaluated})")
            
        except KeyboardInterrupt:
            print(f"\n\n⏹️ Single agent re-validation interrupted by user.")
            print(f"📊 Progress so far:")
            print(f"   ✅ Completed: {completed_validations}")
            print(f"   ❌ Failed: {failed_validations}")
            print(f"   ⏭️ Remaining: {len(project_names) - i}")
            return
            
        except Exception as e:
            print(f"❌ Error re-validating {project_name}: {e}")
            failed_validations += 1
        
        # Progress indicator
        remaining = len(project_names) - i
        if remaining > 0:
            print(f"\n⏳ {remaining} projects remaining...")
    
    # Final summary
    print(f"\n{'🏁' * 60}")
    print(f"📊 {agent_name.upper()} AGENT RE-VALIDATION COMPLETE")
    print(f"{'🏁' * 60}")
    
    print(f"✅ Completed re-validations: {completed_validations}")
    print(f"❌ Failed re-validations: {failed_validations}")
    print(f"📈 Total projects processed: {len(project_names)}")
    
    if completed_validations > 0:
        print(f"\n💾 Updated validation files saved in: {validation_dir}")
        print(f"🔄 Run scoring to see updated results: python calculate_scores.py")


def main():
    """Example usage - choose which agent to process or validate."""
    print("🎯 Single Agent Processor & Validator")
    print("=" * 50)

    print("Choose operation:")
    print("1. Process Basic Agent (generate results)")
    print("2. Process Function Agent (generate results)")
    print("3. Process Expert Agent (generate results)")
    print("4. Process Feedback Agent (generate results)")
    print("5. Re-validate Basic Agent only")
    print("6. Re-validate Function Agent only")
    print("7. Re-validate Expert Agent only")
    print("8. Re-validate Feedback Agent only")

    choice = input("\nEnter your choice (1-8): ").strip()

    if choice == "1":
        process_basic_agent()
    elif choice == "2":
        process_function_agent()
    elif choice == "3":
        process_expert_agent()
    elif choice == "4":
        process_feedback_agent()
    elif choice == "5":
        validate_single_agent_for_all_projects("Basic")
    elif choice == "6":
        validate_single_agent_for_all_projects("Function")
    elif choice == "7":
        validate_single_agent_for_all_projects("Expert")
    elif choice == "8":
        validate_single_agent_for_all_projects("Feedback")
    else:
        print("❌ Invalid choice. Please run again and choose 1-7.")


if __name__ == "__main__":
    main()
