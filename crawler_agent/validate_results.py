#!/usr/bin/env python3
"""
Interactive validation script for three-agent extraction results.
Allows manual validation of each extracted field and saves results to validation files.
"""

import os
import json
import random
from datetime import datetime


def create_validation_directory():
    """Create validation directory if it doesn't exist."""
    validation_dir = "results/validation"
    if not os.path.exists(validation_dir):
        os.makedirs(validation_dir)
        print(f"Created directory: {validation_dir}")
    return validation_dir


def load_project_results(project_name):
    """Load results from all three agents for a project."""
    basic_file = f"results/basic/{project_name}_basic.json"
    function_file = f"results/function/{project_name}_function.json"
    expert_file = f"results/expert/{project_name}_expert.json"

    basic_data = None
    function_data = None
    expert_data = None

    if os.path.exists(basic_file):
        with open(basic_file, 'r', encoding='utf-8') as f:
            basic_data = json.load(f)

    if os.path.exists(function_file):
        with open(function_file, 'r', encoding='utf-8') as f:
            function_data = json.load(f)

    if os.path.exists(expert_file):
        with open(expert_file, 'r', encoding='utf-8') as f:
            expert_data = json.load(f)

    return basic_data, function_data, expert_data


def extract_project_fields(data):
    """Extract project fields from nested data structure."""
    if not data:
        return {}

    # Handle different data structures
    if isinstance(data, dict):
        # Look for common object names
        for key in ["project", "data", "product", "item"]:
            if key in data:
                if isinstance(data[key], dict):
                    return data[key]

        # If no nested structure, return the data itself
        return data

    return {}


def format_field_value(field_value):
    """Format field value for display."""
    if field_value is None:
        return "❌ NULL/MISSING"
    elif isinstance(field_value, str) and len(field_value.strip()) == 0:
        return "❌ EMPTY STRING"
    else:
        return str(field_value)


def get_user_validation_three_agents(field_name, basic_value, function_value, expert_value):
    """Get user validation for three agent results."""
    print(f"\n📋 Field: {field_name}")

    basic_display = format_field_value(basic_value)
    function_display = format_field_value(function_value)
    expert_display = format_field_value(expert_value)

    # Check if all values are the same
    values = [basic_value, function_value, expert_value]
    displays = [basic_display, function_display, expert_display]

    # Normalize for comparison (handle None vs empty string)
    normalized_values = []
    for val in values:
        if val is None or (isinstance(val, str) and val.strip() == ""):
            normalized_values.append(None)
        elif isinstance(val, str):
            normalized_values.append(val.strip())
        else:
            normalized_values.append(val)

    # Check if all are the same
    if len(set(str(v) for v in normalized_values)) == 1:
        # All agents have the same value
        print(f"🤖 All agents: {basic_display}")

        while True:
            user_input = input("✅ Is this correct? (t=true/f=false/s=skip): ").lower().strip()
            if user_input in ['t', 'true']:
                return [True, True, True]  # All correct
            elif user_input in ['f', 'false']:
                return [False, False, False]  # All incorrect
            elif user_input in ['s', 'skip']:
                return [None, None, None]  # All skipped
            else:
                print("❌ Invalid input. Please use 't', 'f', or 's'.")

    else:
        # Values differ - show all three with randomized order
        agents = ["Basic", "Function", "Expert"]
        agent_values = [basic_value, function_value, expert_value]
        agent_displays = [basic_display, function_display, expert_display]

        # Create randomized display order
        combined = list(zip(agents, agent_values, agent_displays))
        random.shuffle(combined)

        # Track which positions correspond to which agents
        position_to_agent = {}

        print("🤖 Agent results:")
        for i, (agent, value, display) in enumerate(combined, 1):
            print(f"   {i}. {display}")
            # Find original agent index
            original_idx = agents.index(agent)
            position_to_agent[i] = original_idx

        while True:
            user_input = input("✅ Which are correct? (1/2/3/multiple like '1,3'/none/skip): ").lower().strip()

            if user_input == 'skip' or user_input == 's':
                return [None, None, None]
            elif user_input == 'none' or user_input == 'n':
                return [False, False, False]
            else:
                try:
                    # Parse selection
                    if ',' in user_input:
                        selections = [int(x.strip()) for x in user_input.split(',')]
                    else:
                        selections = [int(user_input)]

                    # Validate selections
                    if all(1 <= sel <= 3 for sel in selections):
                        # Initialize all as False
                        results = [False, False, False]

                        # Mark selected positions as True
                        for sel in selections:
                            original_agent_idx = position_to_agent[sel]
                            results[original_agent_idx] = True

                        return results
                    else:
                        print("❌ Invalid selection. Use numbers 1-3.")

                except ValueError:
                    print("❌ Invalid input. Use numbers or 'skip'/'none'.")


def validate_project(project_name):
    """Validate extraction results for a project."""
    print(f"\n{'=' * 60}")
    print(f"🔍 VALIDATING PROJECT: {project_name}")
    print(f"{'=' * 60}")

    # Load data from all three agents
    basic_data, function_data, expert_data = load_project_results(project_name)

    if not any([basic_data, function_data, expert_data]):
        print(f"❌ No data found for project '{project_name}'")
        return None

    # Extract project fields
    basic_fields = extract_project_fields(basic_data)
    function_fields = extract_project_fields(function_data)
    expert_fields = extract_project_fields(expert_data)

    print(f"📊 Data loaded:")
    print(f"   Basic Agent: {'✅' if basic_data else '❌'} ({len(basic_fields)} fields)")
    print(f"   Function Agent: {'✅' if function_data else '❌'} ({len(function_fields)} fields)")
    print(f"   Expert Agent: {'✅' if expert_data else '❌'} ({len(expert_fields)} fields)")

    # Get all unique field names
    all_fields = set()
    all_fields.update(basic_fields.keys())
    all_fields.update(function_fields.keys())
    all_fields.update(expert_fields.keys())

    if not all_fields:
        print("❌ No fields found to validate")
        return None

    print(f"\n🎯 Total fields to validate: {len(all_fields)}")
    print("📝 Instructions:")
    print("   • When values are same: t=true, f=false, s=skip")
    print("   • When values differ: select correct numbers (e.g., '1', '1,3', 'none')")

    # Validation results
    validation_results = {
        "project_name": project_name,
        "validation_date": datetime.now().isoformat(),
        "basic_agent": {"correct": 0, "incorrect": 0, "skipped": 0},
        "function_agent": {"correct": 0, "incorrect": 0, "skipped": 0},
        "expert_agent": {"correct": 0, "incorrect": 0, "skipped": 0},
        "field_validations": {}
    }

    # Validate each field
    for field_name in sorted(all_fields):
        basic_value = basic_fields.get(field_name)
        function_value = function_fields.get(field_name)
        expert_value = expert_fields.get(field_name)

        # Get user validation
        results = get_user_validation_three_agents(field_name, basic_value, function_value, expert_value)

        # Store results
        validation_results["field_validations"][field_name] = {
            "basic_value": basic_value,
            "function_value": function_value,
            "expert_value": expert_value,
            "basic_correct": results[0],
            "function_correct": results[1],
            "expert_correct": results[2]
        }

        # Update counters
        for i, (agent_key, result) in enumerate(zip(
                ["basic_agent", "function_agent", "expert_agent"], results
        )):
            if result is True:
                validation_results[agent_key]["correct"] += 1
            elif result is False:
                validation_results[agent_key]["incorrect"] += 1
            else:  # None (skipped)
                validation_results[agent_key]["skipped"] += 1

    return validation_results


def save_validation_results(validation_results):
    """Save validation results to file."""
    if not validation_results:
        return

    validation_dir = create_validation_directory()
    project_name = validation_results["project_name"]
    filename = f"{project_name}_validation.json"
    filepath = os.path.join(validation_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(validation_results, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Validation results saved to: {filepath}")


def print_validation_summary(validation_results):
    """Print a summary of validation results."""
    if not validation_results:
        return

    print(f"\n{'=' * 60}")
    print("📊 VALIDATION SUMMARY")
    print(f"{'=' * 60}")

    agents = ["basic_agent", "function_agent", "expert_agent"]
    agent_names = ["Basic Agent", "Function Agent", "Expert Agent"]

    for agent_key, agent_name in zip(agents, agent_names):
        stats = validation_results[agent_key]
        total = stats["correct"] + stats["incorrect"] + stats["skipped"]
        evaluated = stats["correct"] + stats["incorrect"]

        if evaluated > 0:
            accuracy = (stats["correct"] / evaluated) * 100
            print(f"\n🤖 {agent_name}:")
            print(f"   ✅ Correct: {stats['correct']}")
            print(f"   ❌ Incorrect: {stats['incorrect']}")
            print(f"   ⏭️ Skipped: {stats['skipped']}")
            print(f"   📊 Accuracy: {accuracy:.1f}% ({stats['correct']}/{evaluated})")
        else:
            print(f"\n🤖 {agent_name}: No evaluations (all skipped)")


def main(project_name):
    print("🎯 Three-Agent Validation Tool")
    print("=" * 40)

    # Validate the project
    validation_results = validate_project(project_name)

    if validation_results:
        # Save results
        save_validation_results(validation_results)

        # Print summary
        print_validation_summary(validation_results)

        print(f"\n🏁 Validation complete for project: {project_name}")
    else:
        print(f"\n❌ Validation failed for project: {project_name}")


def validate_all_projects():
    """Validate all projects that have comparison results."""
    print("🚀 Starting Batch Validation for All Projects")
    print("=" * 60)
    
    # Get all projects that have comparison results
    comparison_dir = "results/comparison"
    if not os.path.exists(comparison_dir):
        print(f"❌ Comparison directory not found: {comparison_dir}")
        print("💡 Run comparison first using: python compare_agents.py")
        return
    
    # Find all comparison files and extract project names
    project_names = []
    for filename in os.listdir(comparison_dir):
        if filename.endswith('_comparison.json') and filename != 'batch_summary.json':
            project_name = filename[:-16]  # Remove _comparison.json
            project_names.append(project_name)
    
    if not project_names:
        print(f"❌ No comparison files found in {comparison_dir}")
        print("💡 Run comparison first using: python compare_agents.py")
        return
    
    project_names.sort()  # Sort alphabetically for consistent processing
    
    print(f"📁 Found {len(project_names)} projects with results:")
    for i, project_name in enumerate(project_names, 1):
        print(f"   {i}. {project_name}")
    
    # Check which projects already have validations
    validation_dir = "results/validation"
    existing_validations = []
    pending_validations = []
    
    for project_name in project_names:
        validation_file = os.path.join(validation_dir, f"{project_name}_validation.json")
        if os.path.exists(validation_file):
            existing_validations.append(project_name)
        else:
            pending_validations.append(project_name)
    
    if existing_validations:
        print(f"\n✅ Projects with existing validations ({len(existing_validations)}):")
        for project_name in existing_validations:
            print(f"   • {project_name}")
    
    if not pending_validations:
        print(f"\n🎉 All projects already validated!")
        return
    
    print(f"\n⏳ Projects pending validation ({len(pending_validations)}):")
    for i, project_name in enumerate(pending_validations, 1):
        print(f"   {i}. {project_name}")
    
    print(f"\n📝 Batch Validation Instructions:")
    print("   • This is interactive - you'll validate each field manually")
    print("   • When values are same: t=true, f=false, s=skip")
    print("   • When values differ: select correct numbers (e.g., '1', '1,3', 'none')")
    print("   • You can quit anytime with Ctrl+C")
    
    proceed = input(f"\n🤔 Proceed with validating {len(pending_validations)} projects? (y/n): ").lower().strip()
    if proceed not in ['y', 'yes']:
        print("❌ Batch validation cancelled.")
        return
    
    print(f"\n⏱️ Starting batch validation...")
    
    # Track overall results
    completed_validations = 0
    failed_validations = 0
    skipped_validations = 0
    
    # Process each pending project
    for i, project_name in enumerate(pending_validations, 1):
        print(f"\n{'🔄' * 60}")
        print(f"📋 Validating Project {i}/{len(pending_validations)}: {project_name}")
        print(f"{'🔄' * 60}")
        
        try:
            # Run validation for this project
            validation_results = validate_project(project_name)
            
            if validation_results:
                save_validation_results(validation_results)
                print_validation_summary(validation_results)
                completed_validations += 1
                print(f"✅ Validation completed for {project_name}")
            else:
                failed_validations += 1
                print(f"❌ Validation failed for {project_name}")
            
        except KeyboardInterrupt:
            print(f"\n\n⏹️ Batch validation interrupted by user.")
            print(f"📊 Progress so far:")
            print(f"   ✅ Completed: {completed_validations}")
            print(f"   ❌ Failed: {failed_validations}")
            print(f"   ⏭️ Remaining: {len(pending_validations) - i}")
            return
            
        except Exception as e:
            print(f"❌ Error validating {project_name}: {e}")
            failed_validations += 1
        
        # Progress indicator
        remaining = len(pending_validations) - i
        if remaining > 0:
            print(f"\n⏳ {remaining} projects remaining...")
    
    # Final summary
    print(f"\n{'🏁' * 60}")
    print("📊 BATCH VALIDATION COMPLETE")
    print(f"{'🏁' * 60}")
    
    print(f"✅ Completed validations: {completed_validations}")
    print(f"❌ Failed validations: {failed_validations}")
    print(f"📈 Total projects processed: {len(pending_validations)}")
    
    if completed_validations > 0:
        print(f"\n💾 Validation files saved in: {validation_dir}")
        print(f"🔄 Run scoring next: python calculate_scores.py")


if __name__ == "__main__":
    validate_all_projects()
