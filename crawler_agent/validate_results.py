#!/usr/bin/env python3
"""
Interactive validation script for agent extraction results.
Allows manual validation of each extracted field and saves results to validation files.
"""

import os
import json
import sys
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
    """Load both simple and advanced agent results for a project."""
    simple_file = f"results/simple/{project_name}_simple.json"
    advanced_file = f"results/advanced/{project_name}_advanced.json"
    
    simple_data = None
    advanced_data = None
    
    if os.path.exists(simple_file):
        with open(simple_file, 'r', encoding='utf-8') as f:
            simple_data = json.load(f)
    
    if os.path.exists(advanced_file):
        with open(advanced_file, 'r', encoding='utf-8') as f:
            advanced_data = json.load(f)
    
    return simple_data, advanced_data


def extract_project_fields(data):
    """Extract project fields from nested data structure."""
    if not data:
        return {}
    
    # Handle different data structures
    if isinstance(data, dict):
        if "data" in data and isinstance(data["data"], dict):
            if "project" in data["data"]:
                return data["data"]["project"]
            else:
                return data["data"]
        elif "project" in data:
            return data["project"]
        else:
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


def get_user_validation_comparison(field_name, simple_value, advanced_value):
    """Get user validation when comparing both agent results."""
    print(f"\n📋 Field: {field_name}")
    
    simple_display = format_field_value(simple_value)
    advanced_display = format_field_value(advanced_value)
    
    # Check if values are the same (considering None and empty string differences)
    values_are_same = False
    if simple_value == advanced_value:
        values_are_same = True
    elif (simple_value is None and advanced_value == "") or (advanced_value is None and simple_value == ""):
        values_are_same = True
    elif isinstance(simple_value, str) and isinstance(advanced_value, str):
        if simple_value.strip() == advanced_value.strip():
            values_are_same = True
    
    if values_are_same:
        # Show single value with t/f options
        print(f"🤖 Both agents: {simple_display}")
        
        while True:
            user_input = input("✅ Is this correct? (t=true/f=false/s=skip): ").lower().strip()
            if user_input in ['t', 'true']:
                return True, True  # Both correct
            elif user_input in ['f', 'false']:
                return False, False  # Both incorrect
            elif user_input in ['s', 'skip']:
                return None, None  # Both skipped
            else:
                print("⚠️ Please enter 't' for true, 'f' for false, or 's' to skip")
    else:
        # Randomize the order to avoid bias
        if random.choice([True, False]):
            # Simple first
            print(f"🤖 Agent 1: {simple_display}")
            print(f"🤖 Agent 2: {advanced_display}")
            first_is_simple = True
        else:
            # Advanced first
            print(f"🤖 Agent 1: {advanced_display}")
            print(f"🤖 Agent 2: {simple_display}")
            first_is_simple = False
        
        while True:
            user_input = input("✅ Which is correct? (1=first/2=second/b=both/n=neither/s=skip): ").lower().strip()
            if user_input == '1':
                if first_is_simple:
                    return True, False  # Simple correct, Advanced incorrect
                else:
                    return False, True  # Simple incorrect, Advanced correct
            elif user_input == '2':
                if first_is_simple:
                    return False, True  # Simple incorrect, Advanced correct
                else:
                    return True, False  # Simple correct, Advanced incorrect
            elif user_input in ['b', 'both']:
                return True, True  # Both correct
            elif user_input in ['n', 'neither']:
                return False, False  # Both incorrect
            elif user_input in ['s', 'skip']:
                return None, None  # Both skipped
            else:
                print("⚠️ Please enter '1', '2', 'b' (both), 'n' (neither), or 's' (skip)")


def validate_project(project_name):
    """Validate extraction results for a single project."""
    print(f"\n{'='*60}")
    print(f"🔍 VALIDATING PROJECT: {project_name.upper()}")
    print(f"{'='*60}")
    
    # Load project results
    simple_data, advanced_data = load_project_results(project_name)
    
    if not simple_data and not advanced_data:
        print(f"❌ No results found for project: {project_name}")
        return None
    
    # Extract project fields
    simple_fields = extract_project_fields(simple_data)
    advanced_fields = extract_project_fields(advanced_data)
    
    # Get all unique field names
    all_fields = set()
    if simple_fields:
        all_fields.update(simple_fields.keys())
    if advanced_fields:
        all_fields.update(advanced_fields.keys())
    
    if not all_fields:
        print(f"❌ No fields found in results for project: {project_name}")
        return None
    
    # Initialize validation results
    validation_results = {
        "project_name": project_name,
        "validation_timestamp": datetime.now().isoformat(),
        "simple_agent": {
            "available": simple_data is not None,
            "field_validations": {}
        },
        "advanced_agent": {
            "available": advanced_data is not None,
            "field_validations": {}
        }
    }
    
    print(f"📊 Found {len(all_fields)} fields to validate: {', '.join(sorted(all_fields))}")
    print(f"🤖 Simple Agent: {'✅ Available' if simple_data else '❌ Not available'}")
    print(f"🤖 Advanced Agent: {'✅ Available' if advanced_data else '❌ Not available'}")
    
    # Validate each field for both agents
    for field_name in sorted(all_fields):
        print(f"\n{'-'*40}")
        print(f"🔍 VALIDATING FIELD: {field_name}")
        print(f"{'-'*40}")
        
        # Get values from both agents
        simple_value = simple_fields.get(field_name) if simple_data else None
        advanced_value = advanced_fields.get(field_name) if advanced_data else None
        
        # Handle cases where only one agent has data
        if simple_data and not advanced_data:
            # Only simple agent available
            simple_display = format_field_value(simple_value)
            print(f"🤖 Simple Agent: {simple_display}")
            
            while True:
                user_input = input("✅ Is this correct? (t=true/f=false/s=skip): ").lower().strip()
                if user_input in ['t', 'true']:
                    simple_validation = True
                    break
                elif user_input in ['f', 'false']:
                    simple_validation = False
                    break
                elif user_input in ['s', 'skip']:
                    simple_validation = None
                    break
                else:
                    print("⚠️ Please enter 't' for true, 'f' for false, or 's' to skip")
            
            validation_results["simple_agent"]["field_validations"][field_name] = {
                "value": simple_value,
                "is_correct": simple_validation
            }
            
        elif advanced_data and not simple_data:
            # Only advanced agent available
            advanced_display = format_field_value(advanced_value)
            print(f"🤖 Advanced Agent: {advanced_display}")
            
            while True:
                user_input = input("✅ Is this correct? (t=true/f=false/s=skip): ").lower().strip()
                if user_input in ['t', 'true']:
                    advanced_validation = True
                    break
                elif user_input in ['f', 'false']:
                    advanced_validation = False
                    break
                elif user_input in ['s', 'skip']:
                    advanced_validation = None
                    break
                else:
                    print("⚠️ Please enter 't' for true, 'f' for false, or 's' to skip")
            
            validation_results["advanced_agent"]["field_validations"][field_name] = {
                "value": advanced_value,
                "is_correct": advanced_validation
            }
            
        elif simple_data and advanced_data:
            # Both agents available - use comparison function
            simple_validation, advanced_validation = get_user_validation_comparison(
                field_name, simple_value, advanced_value
            )
            
            validation_results["simple_agent"]["field_validations"][field_name] = {
                "value": simple_value,
                "is_correct": simple_validation
            }
            validation_results["advanced_agent"]["field_validations"][field_name] = {
                "value": advanced_value,
                "is_correct": advanced_validation
            }
    
    return validation_results


def save_validation_results(validation_results, validation_dir):
    """Save validation results to a JSON file."""
    if not validation_results:
        return None
    
    project_name = validation_results["project_name"]
    validation_file = os.path.join(validation_dir, f"{project_name}_validation.json")
    
    with open(validation_file, 'w', encoding='utf-8') as f:
        json.dump(validation_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Validation results saved to: {validation_file}")
    return validation_file


def print_validation_summary(validation_results):
    """Print a summary of validation results."""
    if not validation_results:
        return
    
    print(f"\n📊 VALIDATION SUMMARY FOR {validation_results['project_name'].upper()}")
    print("=" * 50)
    
    for agent_name in ["simple_agent", "advanced_agent"]:
        agent_data = validation_results[agent_name]
        if not agent_data["available"]:
            print(f"🤖 {agent_name.replace('_', ' ').title()}: Not available")
            continue
        
        validations = agent_data["field_validations"]
        correct_count = sum(1 for v in validations.values() if v["is_correct"] is True)
        incorrect_count = sum(1 for v in validations.values() if v["is_correct"] is False)
        skipped_count = sum(1 for v in validations.values() if v["is_correct"] is None)
        total_count = len(validations)
        
        print(f"🤖 {agent_name.replace('_', ' ').title()}:")
        print(f"   ✅ Correct: {correct_count}/{total_count}")
        print(f"   ❌ Incorrect: {incorrect_count}/{total_count}")
        print(f"   ⏭️ Skipped: {skipped_count}/{total_count}")
        if total_count > 0:
            accuracy = (correct_count / (correct_count + incorrect_count)) * 100 if (correct_count + incorrect_count) > 0 else 0
            print(f"   📈 Accuracy: {accuracy:.1f}% (excluding skipped)")


def main(project_name):
    """Main function to run interactive validation."""

    print("🚀 AGENT RESULTS VALIDATION SYSTEM")
    print("=" * 50)
    print("This script helps you validate the accuracy of agent extractions.")
    print("")
    print("🔍 Validation Options:")
    print("  • When values are the same: t=true, f=false, s=skip")
    print("  • When values differ: 1=first, 2=second, b=both correct, n=neither, s=skip")
    print("  • Agents are shown as 'Agent 1' and 'Agent 2' (order is randomized)")
    print("")
    
    # Create validation directory
    validation_dir = create_validation_directory()
    
    # Check if validation already exists
    existing_validation = os.path.join(validation_dir, f"{project_name}_validation.json")
    if os.path.exists(existing_validation):
        overwrite = input(f"\n⚠️ Validation file already exists: {existing_validation}\nOverwrite? (y/n): ")
        if overwrite.lower().strip() not in ['y', 'yes']:
            print("❌ Validation cancelled.")
            sys.exit(0)
    
    # Validate project
    validation_results = validate_project(project_name)
    
    if validation_results:
        # Save results
        save_validation_results(validation_results, validation_dir)
        
        # Print summary
        print_validation_summary(validation_results)
        
        print(f"\n🎉 Validation completed for project: {project_name}")
        print("Use the scoring script to calculate overall scores across projects.")
    else:
        print(f"❌ Validation failed for project: {project_name}")
        sys.exit(1)


if __name__ == "__main__":
    project_name = "halalfund"
    main(project_name)
