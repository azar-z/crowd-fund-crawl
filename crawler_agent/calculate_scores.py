#!/usr/bin/env python3
"""
Scoring calculator for agent performance across all validated projects.
Calculates scores from validation files and outputs performance metrics.
"""

import os
import json
import glob
from datetime import datetime
from typing import Dict, List, Tuple


def load_validation_files():
    """Load all validation files from the validation directory."""
    validation_dir = "results/validation"
    if not os.path.exists(validation_dir):
        print(f"❌ Validation directory not found: {validation_dir}")
        print("Run validate_results.py first to create validation data.")
        return []
    
    validation_files = glob.glob(os.path.join(validation_dir, "*_validation.json"))
    
    if not validation_files:
        print(f"❌ No validation files found in: {validation_dir}")
        print("Run validate_results.py for projects first.")
        return []
    
    validation_data = []
    for file_path in validation_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                validation_data.append(data)
        except Exception as e:
            print(f"⚠️ Error loading {file_path}: {e}")
    
    return validation_data


def calculate_agent_scores(validation_data: List[Dict]) -> Dict:
    """Calculate scores for both agents across all projects."""
    agent_stats = {
        "simple_agent": {
            "total_fields": 0,
            "correct_fields": 0,
            "incorrect_fields": 0,
            "skipped_fields": 0,
            "projects_with_data": 0,
            "field_scores": {}
        },
        "advanced_agent": {
            "total_fields": 0,
            "correct_fields": 0,
            "incorrect_fields": 0,
            "skipped_fields": 0,
            "projects_with_data": 0,
            "field_scores": {}
        }
    }
    
    project_details = []
    
    for project_data in validation_data:
        project_name = project_data.get("project_name", "Unknown")
        project_detail = {
            "project_name": project_name,
            "simple_agent": {"available": False, "score": 0, "details": {}},
            "advanced_agent": {"available": False, "score": 0, "details": {}}
        }
        
        for agent_name in ["simple_agent", "advanced_agent"]:
            agent_data = project_data.get(agent_name, {})
            
            if not agent_data.get("available", False):
                continue
            
            agent_stats[agent_name]["projects_with_data"] += 1
            project_detail[agent_name]["available"] = True
            
            validations = agent_data.get("field_validations", {})
            
            project_correct = 0
            project_total = 0
            project_field_details = {}
            
            for field_name, validation in validations.items():
                is_correct = validation.get("is_correct")
                field_value = validation.get("value")
                
                project_field_details[field_name] = {
                    "value": field_value,
                    "is_correct": is_correct
                }
                
                if is_correct is True:
                    agent_stats[agent_name]["correct_fields"] += 1
                    project_correct += 1
                    project_total += 1
                    
                    # Track field-specific accuracy
                    if field_name not in agent_stats[agent_name]["field_scores"]:
                        agent_stats[agent_name]["field_scores"][field_name] = {"correct": 0, "total": 0}
                    agent_stats[agent_name]["field_scores"][field_name]["correct"] += 1
                    agent_stats[agent_name]["field_scores"][field_name]["total"] += 1
                    
                elif is_correct is False:
                    agent_stats[agent_name]["incorrect_fields"] += 1
                    project_total += 1
                    
                    # Track field-specific accuracy
                    if field_name not in agent_stats[agent_name]["field_scores"]:
                        agent_stats[agent_name]["field_scores"][field_name] = {"correct": 0, "total": 0}
                    agent_stats[agent_name]["field_scores"][field_name]["total"] += 1
                    
                elif is_correct is None:
                    agent_stats[agent_name]["skipped_fields"] += 1
                
                agent_stats[agent_name]["total_fields"] += 1
            
            # Calculate project score (0-100)
            if project_total > 0:
                project_score = (project_correct / project_total) * 100
            else:
                project_score = 0
            
            project_detail[agent_name]["score"] = project_score
            project_detail[agent_name]["details"] = project_field_details
        
        project_details.append(project_detail)
    
    return agent_stats, project_details


def calculate_final_scores(agent_stats: Dict) -> Tuple[float, float]:
    """Calculate final scores (0-100) for both agents."""
    simple_score = 0
    advanced_score = 0
    
    for agent_name, stats in agent_stats.items():
        total_evaluated = stats["correct_fields"] + stats["incorrect_fields"]
        
        if total_evaluated > 0:
            accuracy = (stats["correct_fields"] / total_evaluated) * 100
        else:
            accuracy = 0
        
        if agent_name == "simple_agent":
            simple_score = accuracy
        else:
            advanced_score = accuracy
    
    return simple_score, advanced_score


def print_detailed_report(agent_stats: Dict, project_details: List[Dict]):
    """Print a detailed scoring report."""
    print("\n" + "="*80)
    print("📊 AGENT PERFORMANCE SCORING REPORT")
    print("="*80)
    
    # Overall summary
    simple_score, advanced_score = calculate_final_scores(agent_stats)
    
    print(f"\n🏆 FINAL SCORES (0-100):")
    print(f"   🔹 Simple Agent:   {simple_score:.1f}")
    print(f"   🔹 Advanced Agent: {advanced_score:.1f}")
    
    if simple_score > advanced_score:
        winner = "Simple Agent"
        difference = simple_score - advanced_score
    elif advanced_score > simple_score:
        winner = "Advanced Agent"
        difference = advanced_score - simple_score
    else:
        winner = "TIE"
        difference = 0
    
    print(f"   🏅 Winner: {winner}" + (f" (+{difference:.1f})" if difference > 0 else ""))
    
    # Detailed agent statistics
    print(f"\n📈 DETAILED STATISTICS:")
    print("-" * 50)
    
    for agent_name, stats in agent_stats.items():
        agent_display = agent_name.replace("_", " ").title()
        print(f"\n🤖 {agent_display}:")
        print(f"   Projects with data: {stats['projects_with_data']}")
        print(f"   Total fields evaluated: {stats['correct_fields'] + stats['incorrect_fields']}")
        print(f"   ✅ Correct: {stats['correct_fields']}")
        print(f"   ❌ Incorrect: {stats['incorrect_fields']}")
        print(f"   ⏭️ Skipped: {stats['skipped_fields']}")
        
        total_evaluated = stats["correct_fields"] + stats["incorrect_fields"]
        if total_evaluated > 0:
            accuracy = (stats["correct_fields"] / total_evaluated) * 100
            print(f"   📊 Accuracy: {accuracy:.1f}%")
        else:
            print(f"   📊 Accuracy: N/A (no evaluated fields)")
    
    # Field-specific performance
    print(f"\n🎯 FIELD-SPECIFIC PERFORMANCE:")
    print("-" * 50)
    
    all_fields = set()
    for agent_name, stats in agent_stats.items():
        all_fields.update(stats["field_scores"].keys())
    
    for field_name in sorted(all_fields):
        print(f"\n📋 {field_name}:")
        for agent_name, stats in agent_stats.items():
            agent_display = agent_name.replace("_", " ").title()
            if field_name in stats["field_scores"]:
                field_stats = stats["field_scores"][field_name]
                accuracy = (field_stats["correct"] / field_stats["total"]) * 100
                print(f"   {agent_display}: {field_stats['correct']}/{field_stats['total']} ({accuracy:.1f}%)")
            else:
                print(f"   {agent_display}: No data")
    
    # Project-by-project breakdown
    print(f"\n📂 PROJECT-BY-PROJECT SCORES:")
    print("-" * 50)
    
    for project in project_details:
        project_name = project["project_name"]
        simple_available = project["simple_agent"]["available"]
        advanced_available = project["advanced_agent"]["available"]
        
        print(f"\n📁 {project_name}:")
        if simple_available:
            simple_score = project["simple_agent"]["score"]
            print(f"   Simple Agent: {simple_score:.1f}%")
        else:
            print(f"   Simple Agent: No data")
        
        if advanced_available:
            advanced_score = project["advanced_agent"]["score"]
            print(f"   Advanced Agent: {advanced_score:.1f}%")
        else:
            print(f"   Advanced Agent: No data")


def save_scoring_report(agent_stats: Dict, project_details: List[Dict]):
    """Save the scoring report to a JSON file."""
    simple_score, advanced_score = calculate_final_scores(agent_stats)
    
    report = {
        "report_timestamp": datetime.now().isoformat(),
        "final_scores": {
            "simple_agent": simple_score,
            "advanced_agent": advanced_score
        },
        "agent_statistics": agent_stats,
        "project_details": project_details
    }
    
    # Create results directory if it doesn't exist
    results_dir = "results"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    
    report_file = os.path.join(results_dir, "scoring_report.json")
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Scoring report saved to: {report_file}")
    return report_file


def main():
    """Main function to calculate and display scores."""
    print("🚀 AGENT SCORING CALCULATOR")
    print("=" * 50)
    
    # Load validation files
    validation_data = load_validation_files()
    
    if not validation_data:
        print("❌ No validation data found. Exiting.")
        return
    
    print(f"📊 Loaded validation data for {len(validation_data)} projects")
    
    # Calculate scores
    agent_stats, project_details = calculate_agent_scores(validation_data)
    
    # Print detailed report
    print_detailed_report(agent_stats, project_details)
    
    # Save report
    save_scoring_report(agent_stats, project_details)
    
    print(f"\n🎉 Scoring calculation completed!")


if __name__ == "__main__":
    main()
