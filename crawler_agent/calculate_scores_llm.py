#!/usr/bin/env python3
"""
Calculate accuracy scores for three agents based on LLM validation files.
Generates scoring_report_llm.json with LLM-based evaluations.
"""

import os
import json
from typing import Dict, List, Tuple
from datetime import datetime


def find_llm_validation_files():
    """Find all LLM validation files in the llm_validation directory."""
    llm_validation_dir = "results/llm_validation"

    if not os.path.exists(llm_validation_dir):
        print(f"❌ LLM validation directory not found: {llm_validation_dir}")
        print("💡 Run LLM evaluation first: python llm_judge.py")
        return []

    validation_files = []
    for filename in os.listdir(llm_validation_dir):
        if filename.endswith("_llm_validation.json"):
            filepath = os.path.join(llm_validation_dir, filename)
            validation_files.append(filepath)

    return validation_files


def load_llm_validation_data(file_path: str) -> Dict:
    """Load LLM validation data from a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading {file_path}: {e}")
        return {}


def calculate_llm_agent_scores(validation_data: List[Dict]) -> Tuple[Dict, List[Dict]]:
    """Calculate scores for all three agents across all projects based on LLM evaluations."""

    # Initialize agent statistics
    agent_stats = {
        "basic_agent": {
            "correct": 0, 
            "incorrect": 0, 
            "projects": [],
            "total_confidence": 0.0,
            "evaluated_fields": 0
        },
        "function_agent": {
            "correct": 0, 
            "incorrect": 0, 
            "projects": [],
            "total_confidence": 0.0,
            "evaluated_fields": 0
        },
        "expert_agent": {
            "correct": 0, 
            "incorrect": 0, 
            "projects": [],
            "total_confidence": 0.0,
            "evaluated_fields": 0
        }
    }

    project_details = []

    for data in validation_data:
        if not data:
            continue

        project_name = data.get("project_name", "unknown")
        llm_model = data.get("llm_model", "unknown")

        # Project-level details
        project_field_details = {
            "project_name": project_name,
            "evaluation_date": data.get("evaluation_date", ""),
            "llm_model": llm_model,
            "agents": {}
        }

        # Process each agent
        for agent_key in ["basic_agent", "function_agent", "expert_agent"]:
            if agent_key in data:
                agent_data = data[agent_key]

                # Add to overall stats
                agent_stats[agent_key]["correct"] += agent_data.get("correct", 0)
                agent_stats[agent_key]["incorrect"] += agent_data.get("incorrect", 0)
                agent_stats[agent_key]["total_confidence"] += agent_data.get("total_confidence", 0.0)
                agent_stats[agent_key]["projects"].append(project_name)

                # Count evaluated fields for this agent
                evaluated_fields = agent_data.get("correct", 0) + agent_data.get("incorrect", 0)
                agent_stats[agent_key]["evaluated_fields"] += evaluated_fields

                # Calculate project-level accuracy
                correct = agent_data.get("correct", 0)
                incorrect = agent_data.get("incorrect", 0)
                total = correct + incorrect
                avg_confidence = agent_data.get("average_confidence", 0.0)

                accuracy = (correct / total * 100) if total > 0 else 0

                project_field_details["agents"][agent_key] = {
                    "correct": correct,
                    "incorrect": incorrect,
                    "evaluated": total,
                    "accuracy": round(accuracy, 1),
                    "average_confidence": avg_confidence
                }

        project_details.append(project_field_details)

    # Calculate overall average confidence for each agent
    for agent_key in agent_stats:
        total_fields = agent_stats[agent_key]["evaluated_fields"]
        if total_fields > 0:
            overall_avg_confidence = agent_stats[agent_key]["total_confidence"] / total_fields
            agent_stats[agent_key]["overall_average_confidence"] = round(overall_avg_confidence, 3)
        else:
            agent_stats[agent_key]["overall_average_confidence"] = 0.0

    return agent_stats, project_details


def print_llm_detailed_report(agent_stats: Dict, project_details: List[Dict]):
    """Print a comprehensive LLM scoring report."""

    print("🤖 LLM-BASED THREE-AGENT SCORING REPORT")
    print("=" * 60)

    # Overall scores
    agent_names = {
        "basic_agent": "Basic Agent",
        "function_agent": "Function Agent",
        "expert_agent": "Expert Agent"
    }

    print("\n📊 OVERALL PERFORMANCE (LLM Evaluation)")
    print("-" * 40)

    overall_scores = {}
    llm_model = project_details[0].get("llm_model", "unknown") if project_details else "unknown"
    print(f"🧠 LLM Model: {llm_model}")

    for agent_key, agent_name in agent_names.items():
        stats = agent_stats[agent_key]
        total_correct = stats["correct"]
        total_incorrect = stats["incorrect"]
        total_evaluated = total_correct + total_incorrect
        overall_avg_conf = stats.get("overall_average_confidence", 0.0)

        if total_evaluated > 0:
            accuracy = (total_correct / total_evaluated) * 100
            overall_scores[agent_key] = accuracy
        else:
            accuracy = 0
            overall_scores[agent_key] = 0

        print(f"\n🤖 {agent_name}:")
        print(f"   ✅ Correct: {total_correct}")
        print(f"   ❌ Incorrect: {total_incorrect}")
        print(f"   📊 LLM Accuracy: {accuracy:.1f}% ({total_correct}/{total_evaluated})")
        print(f"   🎯 Overall LLM Confidence: {overall_avg_conf:.3f}")
        print(f"   📈 Projects: {len(set(stats['projects']))}")

    # Ranking
    if overall_scores:
        print(f"\n🏆 AGENT RANKING (by LLM accuracy)")
        print("-" * 40)

        sorted_agents = sorted(overall_scores.items(), key=lambda x: x[1], reverse=True)

        for i, (agent_key, score) in enumerate(sorted_agents, 1):
            agent_name = agent_names[agent_key]
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
            print(f"   {medal} {i}. {agent_name}: {score:.1f}%")

    # Project-by-project breakdown
    if project_details:
        print(f"\n📋 PROJECT-BY-PROJECT BREAKDOWN (LLM)")
        print("-" * 40)

        for project in project_details:
            project_name = project["project_name"]
            print(f"\n📁 {project_name}:")

            for agent_key, agent_name in agent_names.items():
                if agent_key in project["agents"]:
                    agent_data = project["agents"][agent_key]
                    accuracy = agent_data["accuracy"]
                    evaluated = agent_data["evaluated"]
                    correct = agent_data["correct"]
                    confidence = agent_data.get("average_confidence", 0.0)

                    print(f"   {agent_name}: {accuracy:.1f}% ({correct}/{evaluated}) conf:{confidence:.3f}")


def save_llm_scoring_report(agent_stats: Dict, project_details: List[Dict]):
    """Save the LLM scoring report to a JSON file."""

    # Calculate final scores
    final_scores = {}
    agent_names = {
        "basic_agent": "Basic Agent",
        "function_agent": "Function Agent",
        "expert_agent": "Expert Agent"
    }

    for agent_key, agent_name in agent_names.items():
        stats = agent_stats[agent_key]
        total_correct = stats["correct"]
        total_incorrect = stats["incorrect"]
        total_evaluated = total_correct + total_incorrect
        overall_avg_conf = stats.get("overall_average_confidence", 0.0)

        if total_evaluated > 0:
            accuracy = (total_correct / total_evaluated) * 100
        else:
            accuracy = 0

        final_scores[agent_key] = {
            "agent_name": agent_name,
            "correct": total_correct,
            "incorrect": total_incorrect,
            "evaluated": total_evaluated,
            "accuracy": round(accuracy, 1),
            "overall_confidence": overall_avg_conf,
            "projects_count": len(set(stats["projects"]))
        }

    # Get LLM model info
    llm_model = project_details[0].get("llm_model", "unknown") if project_details else "unknown"

    # Create report data
    report_data = {
        "report_date": datetime.now().isoformat(),
        "report_type": "llm_based_three_agent_scoring",
        "llm_model": llm_model,
        "evaluation_method": "automated_llm_judgment",
        "overall_scores": final_scores,
        "project_details": project_details,
        "summary": {
            "total_projects": len(project_details),
            "best_agent": max(final_scores.items(), key=lambda x: x[1]["accuracy"])[0] if final_scores else None,
            "avg_confidence_across_agents": round(
                sum(score["overall_confidence"] for score in final_scores.values()) / len(final_scores), 3
            ) if final_scores else 0.0
        },
        "comparison_note": "This report uses LLM-based automatic evaluation instead of human validation"
    }

    # Save to file
    report_file = "results/scoring_report_llm.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    print(f"\n💾 LLM-based scoring report saved to: {report_file}")


def compare_with_human_validation():
    """Compare LLM results with human validation if available."""
    
    human_report_file = "results/scoring_report.json"
    llm_report_file = "results/scoring_report_llm.json"
    
    if not os.path.exists(human_report_file):
        print("\n💡 Human validation report not found. Skipping comparison.")
        return
    
    if not os.path.exists(llm_report_file):
        print("\n💡 LLM report not generated yet. Skipping comparison.")
        return
    
    try:
        with open(human_report_file, 'r', encoding='utf-8') as f:
            human_data = json.load(f)
        
        with open(llm_report_file, 'r', encoding='utf-8') as f:
            llm_data = json.load(f)
        
        print(f"\n📊 HUMAN vs LLM VALIDATION COMPARISON")
        print("-" * 50)
        
        agent_names = {
            "basic_agent": "Basic Agent",
            "function_agent": "Function Agent", 
            "expert_agent": "Expert Agent"
        }
        
        for agent_key, agent_name in agent_names.items():
            if agent_key in human_data.get("overall_scores", {}) and agent_key in llm_data.get("overall_scores", {}):
                human_acc = human_data["overall_scores"][agent_key]["accuracy"]
                llm_acc = llm_data["overall_scores"][agent_key]["accuracy"]
                diff = llm_acc - human_acc
                
                print(f"\n🤖 {agent_name}:")
                print(f"   👤 Human Validation: {human_acc:.1f}%")
                print(f"   🧠 LLM Validation: {llm_acc:.1f}%")
                print(f"   📈 Difference: {diff:+.1f}%")
        
        # Overall correlation
        human_best = human_data.get("summary", {}).get("best_agent", "unknown")
        llm_best = llm_data.get("summary", {}).get("best_agent", "unknown")
        
        print(f"\n🏆 Best Agent Comparison:")
        print(f"   👤 Human: {agent_names.get(human_best, human_best)}")
        print(f"   🧠 LLM: {agent_names.get(llm_best, llm_best)}")
        print(f"   🎯 Agreement: {'✅ Yes' if human_best == llm_best else '❌ No'}")
        
    except Exception as e:
        print(f"❌ Error comparing reports: {e}")


def main():
    """Main function to calculate and display LLM-based scores."""

    print("🤖 LLM-Based Three-Agent Scoring Calculator")
    print("=" * 50)

    # Find LLM validation files
    validation_files = find_llm_validation_files()

    if not validation_files:
        print("❌ No LLM validation files found.")
        print("💡 Run LLM evaluation first: python llm_judge.py")
        return

    print(f"📁 Found {len(validation_files)} LLM validation files")

    # Load all LLM validation data
    all_validation_data = []
    for file_path in validation_files:
        data = load_llm_validation_data(file_path)
        if data:
            all_validation_data.append(data)
            project_name = data.get("project_name", os.path.basename(file_path))
            print(f"   ✅ Loaded: {project_name}")

    if not all_validation_data:
        print("❌ No valid LLM validation data found.")
        return

    # Calculate LLM-based scores
    print(f"\n🔄 Calculating LLM-based scores...")
    agent_stats, project_details = calculate_llm_agent_scores(all_validation_data)

    # Print detailed report
    print_llm_detailed_report(agent_stats, project_details)

    # Save report
    save_llm_scoring_report(agent_stats, project_details)

    # Compare with human validation if available
    compare_with_human_validation()

    print(f"\n🏁 LLM-based scoring calculation complete!")


if __name__ == "__main__":
    main()
