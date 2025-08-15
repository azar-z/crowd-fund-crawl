#!/usr/bin/env python3
"""
Simple comparison script for Basic, Function, and Expert crawler agents.
"""

import os
import json
import time
from dotenv import load_dotenv
from crawler_agent.agents.basic import BasicAgent
from crawler_agent.agents.function import FunctionAgent
from crawler_agent.agents.expert import ExpertAgent


def create_results_directory():
    """Create results directory structure if it doesn't exist."""
    directories = [
        "results",
        "results/basic",
        "results/function",
        "results/expert",
        "results/comparison"
    ]

    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")


def test_agent(agent, agent_name, input_file, config_file, output_file):
    """Test a single agent and return results."""
    print(f"\n{'='*50}")
    print(f"🧪 Testing {agent_name}")
    print(f"{'='*50}")

    start_time = time.time()

    try:
        if not os.path.exists(output_file):
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
                "data": saved_data
            }
        else:
            print(f"❌ {agent_name} failed - no output file created")
            return {
                "agent_name": agent_name,
                "success": False,
                "processing_time": processing_time,
                "data": None
            }

    except Exception as e:
        end_time = time.time()
        processing_time = end_time - start_time
        print(f"❌ {agent_name} failed after {processing_time:.2f} seconds: {e}")
        return {
            "agent_name": agent_name,
            "success": False,
            "processing_time": processing_time,
            "data": None
        }


def compare_agents(project_name):
    """Main function to test all three agents."""
    print("🚀 Starting Three-Agent Comparison Test")
    comparison_output = f"results/comparison/{project_name}_comparison.json"
    if os.path.exists(comparison_output):
        print(f"Comparison file already exists. Skipping {project_name} comparison")
        return

    # Load environment variables
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")

    # Create results directory
    create_results_directory()

    # Configuration
    html_file = f"single_samples/{project_name}.html"
    config_file = "configs/single_project_config.json"

    if not os.path.exists(html_file):
        print(f"❌ HTML file not found: {html_file}")
        return
    if not os.path.exists(config_file):
        print(f"❌ Config file not found: {config_file}")
        return

    print(f"📄 Testing with: {html_file}")
    print(f"⚙️ Using config: {config_file}")

    # Output files
    basic_output = f"results/basic/{project_name}_basic.json"
    function_output = f"results/function/{project_name}_function.json"
    expert_output = f"results/expert/{project_name}_expert.json"

    # Initialize agents
    print("\n🔧 Initializing agents...")
    basic_agent = BasicAgent(api_key=api_key)
    function_agent = FunctionAgent(api_key=api_key)
    expert_agent = ExpertAgent(api_key=api_key)

    # Test all agents
    basic_result = test_agent(basic_agent, "Basic Agent", html_file, config_file, basic_output)
    function_result = test_agent(function_agent, "Function Agent", html_file, config_file, function_output)
    expert_result = test_agent(expert_agent, "Expert Agent", html_file, config_file, expert_output)

    # Summary
    print(f"\n{'='*50}")
    print("📊 COMPARISON SUMMARY")
    print(f"{'='*50}")

    agents = [basic_result, function_result, expert_result]
    successful_agents = [a for a in agents if a["success"]]

    print(f"✅ Successful agents: {len(successful_agents)}/3")
    for agent in successful_agents:
        print(f"   • {agent['agent_name']}: {agent['processing_time']:.2f}s")

    if len(successful_agents) > 1:
        # Find fastest
        fastest = min(successful_agents, key=lambda x: x["processing_time"])
        print(f"\n🏆 Fastest: {fastest['agent_name']} ({fastest['processing_time']:.2f}s)")

    # Save comparison results
    comparison_data = {
        "basic_agent": basic_result,
        "function_agent": function_result,
        "expert_agent": expert_result,
        "summary": {
            "successful_count": len(successful_agents),
            "total_count": 3,
            "fastest_agent": fastest["agent_name"] if successful_agents else None
        }
    }

    with open(comparison_output, 'w', encoding='utf-8') as f:
        json.dump(comparison_data, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Results saved:")
    print(f"   📁 Basic: {basic_output}")
    print(f"   📁 Function: {function_output}")
    print(f"   📁 Expert: {expert_output}")
    print(f"   📁 Comparison: {comparison_output}")

    print(f"\n🏁 Three-Agent Comparison Complete!")


def compare_all_projects():
    """Compare all three agents for all projects in single_samples folder."""
    print("🚀 Starting Batch Comparison for All Projects")
    print("=" * 60)
    
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
    
    print(f"\n⏱️ Starting batch processing...")
    
    # Track overall results
    overall_results = []
    successful_projects = 0
    failed_projects = 0
    
    start_time = time.time()
    
    # Process each project
    for i, project_name in enumerate(project_names, 1):
        print(f"\n{'🔄' * 60}")
        print(f"📋 Processing Project {i}/{len(project_names)}: {project_name}")
        print(f"{'🔄' * 60}")
        
        try:
            # Run comparison for this project
            compare_agents(project_name)
            successful_projects += 1
            overall_results.append({"project": project_name, "status": "success"})
            
        except Exception as e:
            print(f"❌ Failed to process {project_name}: {e}")
            failed_projects += 1
            overall_results.append({"project": project_name, "status": "failed", "error": str(e)})
        
        # Progress indicator
        remaining = len(project_names) - i
        if remaining > 0:
            print(f"\n⏳ {remaining} projects remaining...")
    
    # Final summary
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\n{'🏁' * 60}")
    print("📊 BATCH PROCESSING COMPLETE")
    print(f"{'🏁' * 60}")
    
    print(f"✅ Successful projects: {successful_projects}")
    print(f"❌ Failed projects: {failed_projects}")
    print(f"📈 Total projects: {len(project_names)}")
    print(f"⏱️ Total processing time: {total_time:.2f} seconds")
    print(f"⚡ Average time per project: {total_time/len(project_names):.2f} seconds")
    
    # Save batch summary
    batch_summary = {
        "batch_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_projects": len(project_names),
        "successful_projects": successful_projects,
        "failed_projects": failed_projects,
        "total_time_seconds": total_time,
        "average_time_per_project": total_time / len(project_names),
        "project_results": overall_results
    }
    
    batch_summary_file = "results/comparison/batch_summary.json"
    with open(batch_summary_file, 'w', encoding='utf-8') as f:
        json.dump(batch_summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Batch summary saved to: {batch_summary_file}")
    
    if failed_projects > 0:
        print(f"\n⚠️ Failed projects:")
        for result in overall_results:
            if result["status"] == "failed":
                print(f"   • {result['project']}: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    compare_all_projects()
