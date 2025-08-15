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
    comparison_output = f"results/comparison/{project_name}_comparison.json"
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


if __name__ == "__main__":
    project_name = "ifund"
    compare_agents(project_name)
