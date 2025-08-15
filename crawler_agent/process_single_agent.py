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
    agents = ["basic_agent", "function_agent", "expert_agent"]
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
        agent_name (str): Name of the agent (e.g., "Basic", "Function", "Expert")
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


def main():
    """Example usage - choose which agent to process."""
    print("🎯 Single Agent Processor Examples")
    print("=" * 50)

    print("Choose which agent to process:")
    print("1. Basic Agent (fastest, no function calling)")
    print("2. Function Agent (function calling)")
    print("3. Expert Agent (multi-round, most thorough)")
    print("4. All agents (one by one)")

    choice = input("\nEnter your choice (1-4): ").strip()

    if choice == "1":
        process_basic_agent()
    elif choice == "2":
        process_function_agent()
    elif choice == "3":
        process_expert_agent()
    elif choice == "4":
        process_basic_agent()
        process_function_agent()
        process_expert_agent()
    else:
        print("❌ Invalid choice. Please run again and choose 1-4.")


if __name__ == "__main__":
    main()
