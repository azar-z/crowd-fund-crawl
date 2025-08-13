"""
Comparison script to test both Simple and Advanced crawler agents.
"""

import os
import json
import time
from dotenv import load_dotenv
from crawler_agent.agents.simple import SimpleCrawlerAgent
from crawler_agent.agents.advanced import AdvancedCrawlerAgent


def create_results_directory():
    """Create results directory structure if it doesn't exist."""
    directories = [
        "results",
        "results/simple",
        "results/advanced",
        "results/comparison"
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")


def test_agent(agent, agent_name, html_file, config_file, output_file):
    """
    Test a single agent and return results with timing.
    
    Args:
        agent: The crawler agent to test
        agent_name (str): Name of the agent for logging
        html_file (str): Path to HTML file
        config_file (str): Path to config file
        output_file (str): Path to output file
        
    Returns:
        dict: Test results with timing and success status
    """
    print(f"\n{'='*50}")
    print(f"🧪 Testing {agent_name}")
    print(f"{'='*50}")
    
    start_time = time.time()
    
    try:
        # Remove existing output file if it exists
        # if os.path.exists(output_file):
        #     os.remove(output_file)
        #     print(f"   🗑️ Removed existing output file: {output_file}")

        if not os.path.exists(output_file):
        # Process and save results
            agent.process_and_save(html_file, config_file, output_file)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Load and return the saved results
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
            
            result = {
                "agent_name": agent_name,
                "success": True,
                "processing_time": processing_time,
                "output_file": output_file,
                "data": saved_data,
                "error": None
            }
        else:
            result = {
                "agent_name": agent_name,
                "success": False,
                "processing_time": processing_time,
                "output_file": output_file,
                "data": None,
                "error": "Output file not created"
            }
        
        print(f"✅ {agent_name} completed in {processing_time:.2f} seconds")
        return result
        
    except Exception as e:
        end_time = time.time()
        processing_time = end_time - start_time
        
        result = {
            "agent_name": agent_name,
            "success": False,
            "processing_time": processing_time,
            "output_file": output_file,
            "data": None,
            "error": str(e)
        }
        
        print(f"❌ {agent_name} failed after {processing_time:.2f} seconds: {e}")
        return result


def compare_results(simple_result, advanced_result):
    """
    Compare results from both agents.
    
    Args:
        simple_result (dict): Results from simple agent
        advanced_result (dict): Results from advanced agent
        
    Returns:
        dict: Comparison analysis
    """
    print(f"\n{'='*50}")
    print("📊 COMPARISON ANALYSIS")
    print(f"{'='*50}")
    
    comparison = {
        "simple_agent": {
            "success": simple_result["success"],
            "processing_time": simple_result["processing_time"],
            "error": simple_result["error"]
        },
        "advanced_agent": {
            "success": advanced_result["success"],
            "processing_time": advanced_result["processing_time"],
            "error": advanced_result["error"]
        },
        "analysis": {}
    }
    
    # Performance comparison
    if simple_result["success"] and advanced_result["success"]:
        time_diff = advanced_result["processing_time"] - simple_result["processing_time"]
        comparison["analysis"]["speed"] = {
            "simple_faster": time_diff > 0,
            "time_difference": time_diff,
            # "speed_ratio": advanced_result["processing_time"] / simple_result["processing_time"]
        }
        
        print(f"⏱️ Speed Comparison:")
        print(f"   Simple Agent: {simple_result['processing_time']:.2f}s")
        print(f"   Advanced Agent: {advanced_result['processing_time']:.2f}s")
        print(f"   Difference: {time_diff:+.2f}s")
        
        # Data quality comparison
        simple_data = simple_result["data"]
        advanced_data = advanced_result["data"]
        
        # Extract actual data (handle metadata wrapper)
        if isinstance(advanced_data, dict) and "data" in advanced_data:
            advanced_data = advanced_data["data"]
        
        # Helper function to flatten nested dictionaries
        def flatten_dict(data, parent_key='', sep='.'):
            items = []
            if isinstance(data, dict):
                for k, v in data.items():
                    new_key = f"{parent_key}{sep}{k}" if parent_key else k
                    if isinstance(v, dict):
                        items.extend(flatten_dict(v, new_key, sep=sep).items())
                    else:
                        items.append((new_key, v))
            else:
                items.append((parent_key, data))
            return dict(items)
        
        # Create unified field comparison with flattened fields
        field_comparison = {}
        if simple_data and advanced_data:
            # Flatten both data structures
            simple_flat = flatten_dict(simple_data) if simple_data else {}
            advanced_flat = flatten_dict(advanced_data) if advanced_data else {}
            
            # Get all field paths from both datasets
            all_fields = set(simple_flat.keys()) | set(advanced_flat.keys())
            
            for field in sorted(all_fields):
                simple_val = simple_flat.get(field, None)
                advanced_val = advanced_flat.get(field, None)
                
                # Determine comparison status
                if simple_val == advanced_val:
                    status = "MATCH"
                elif simple_val is None:
                    status = "ADVANCED_ONLY"
                elif advanced_val is None:
                    status = "SIMPLE_ONLY"
                else:
                    status = "DIFFERENT"
                
                field_comparison[field] = {
                    "simple_value": simple_val,
                    "advanced_value": advanced_val,
                    "status": status,
                    "match": status == "MATCH"
                }
        
        # Count flattened fields for more accurate comparison
        simple_flat_count = len(flatten_dict(simple_data)) if simple_data else 0
        advanced_flat_count = len(flatten_dict(advanced_data)) if advanced_data else 0
        
        comparison["analysis"]["data_comparison"] = {
            "simple_fields_count": simple_flat_count,
            "advanced_fields_count": advanced_flat_count,
            "simple_top_level_count": len(simple_data) if simple_data else 0,
            "advanced_top_level_count": len(advanced_data) if advanced_data else 0,
            "field_comparison": field_comparison,
            "simple_data": simple_data,
            "advanced_data": advanced_data
        }
        
        print(f"\n📋 Data Quality Comparison:")
        print(f"   Simple Agent extracted {simple_flat_count} fields ({len(simple_data) if simple_data else 0} top-level)")
        print(f"   Advanced Agent extracted {advanced_flat_count} fields ({len(advanced_data) if advanced_data else 0} top-level)")
        
        # Field-by-field comparison display
        if field_comparison:
            print(f"\n🔍 Field-by-field comparison:")
            
            for field, comparison_data in field_comparison.items():
                status = comparison_data["status"]
                simple_val = comparison_data["simple_value"]
                advanced_val = comparison_data["advanced_value"]
                
                # Display status with emojis
                status_display = {
                    "MATCH": "✅ MATCH",
                    "ADVANCED_ONLY": "🆕 ADVANCED ONLY",
                    "SIMPLE_ONLY": "🔶 SIMPLE ONLY",
                    "DIFFERENT": "🔄 DIFFERENT"
                }
                
                print(f"   {field}: {status_display[status]}")
                if status != "MATCH":
                    print(f"      Simple: {simple_val if simple_val is not None else '❌ MISSING'}")
                    print(f"      Advanced: {advanced_val if advanced_val is not None else '❌ MISSING'}")
    
    elif simple_result["success"] and not advanced_result["success"]:
        print("⚠️ Simple agent succeeded, but Advanced agent failed!")
        comparison["analysis"]["winner"] = "simple"
        
    elif not simple_result["success"] and advanced_result["success"]:
        print("🎉 Advanced agent succeeded, but Simple agent failed!")
        comparison["analysis"]["winner"] = "advanced"
        
    else:
        print("❌ Both agents failed!")
        comparison["analysis"]["winner"] = "none"
    
    return comparison


def main(project_name):
    """
    Main function to run the agent comparison.
    
    Args:
        project_name (str): Name of the project to test (default: "dongi")
    """
    print(f"🚀 Starting Agent Comparison Test for project: {project_name}")
    
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")
    
    # Create results directory
    create_results_directory()
    
    # Define test files based on project name
    html_file = f"single_samples/{project_name}.html"
    config_file = "configs/single_project_config.json"
    
    # Validate that required files exist
    if not os.path.exists(html_file):
        raise FileNotFoundError(f"HTML file not found: {html_file}")
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Config file not found: {config_file}")
    
    print(f"📄 HTML file: {html_file}")
    print(f"⚙️ Config file: {config_file}")
    
    # Output files based on project name
    simple_output = f"results/simple/{project_name}_simple.json"
    advanced_output = f"results/advanced/{project_name}_advanced.json"
    comparison_output = f"results/comparison/{project_name}_comparison.json"
    
    # Initialize agents
    print("🔧 Initializing agents...")
    simple_agent = SimpleCrawlerAgent(api_key=api_key)
    advanced_agent = AdvancedCrawlerAgent(api_key=api_key, max_retries=3, voting_rounds=3)
    
    # Test both agents
    simple_result = test_agent(simple_agent, "Simple Agent", html_file, config_file, simple_output)
    advanced_result = test_agent(advanced_agent, "Advanced Agent", html_file, config_file, advanced_output)
    
    # Compare results
    comparison = compare_results(simple_result, advanced_result)

    # Save comparison results
    with open(comparison_output, 'w', encoding='utf-8') as f:
        json.dump(comparison, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Comparison results saved to: {comparison_output}")
    print(f"📁 Simple agent results: {simple_output}")
    print(f"📁 Advanced agent results: {advanced_output}")

    print(f"\n{'='*50}")
    print("🏁 Comparison Complete!")
    print(f"{'='*50}")


if __name__ == "__main__":
    project_name = "zarincrowd"
    main(project_name)

