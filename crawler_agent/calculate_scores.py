#!/usr/bin/env python3
"""
Calculate accuracy scores for three agents based on validation files.
"""

import os
import json
from typing import Dict, List, Tuple
from datetime import datetime


def find_validation_files():
    """Find all three-agent validation files in the validation directory."""
    validation_dir = "results/validation"

    if not os.path.exists(validation_dir):
        print(f"❌ Validation directory not found: {validation_dir}")
        return []

    validation_files = []
    for filename in os.listdir(validation_dir):
        if filename.endswith("_validation.json"):
            filepath = os.path.join(validation_dir, filename)
            validation_files.append(filepath)

    return validation_files


def load_validation_data(file_path: str) -> Dict:
    """Load validation data from a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading {file_path}: {e}")
        return {}


def calculate_agent_scores(validation_data: List[Dict]) -> Tuple[Dict, List[Dict]]:
    """Calculate scores for all three agents across all projects."""

    # Initialize agent statistics
    agent_stats = {
        "basic_agent": {"correct": 0, "incorrect": 0, "skipped": 0, "projects": []},
        "function_agent": {"correct": 0, "incorrect": 0, "skipped": 0, "projects": []},
        "expert_agent": {"correct": 0, "incorrect": 0, "skipped": 0, "projects": []}
    }

    project_details = []

    for data in validation_data:
        if not data:
            continue

        project_name = data.get("project_name", "unknown")

        # Project-level details
        project_field_details = {
            "project_name": project_name,
            "validation_date": data.get("validation_date", ""),
            "agents": {}
        }

        # Process each agent
        for agent_key in ["basic_agent", "function_agent", "expert_agent"]:
            if agent_key in data:
                agent_data = data[agent_key]

                # Add to overall stats
                agent_stats[agent_key]["correct"] += agent_data.get("correct", 0)
                agent_stats[agent_key]["incorrect"] += agent_data.get("incorrect", 0)
                agent_stats[agent_key]["skipped"] += agent_data.get("skipped", 0)
                agent_stats[agent_key]["projects"].append(project_name)

                # Calculate project-level accuracy
                correct = agent_data.get("correct", 0)
                incorrect = agent_data.get("incorrect", 0)
                skipped = agent_data.get("skipped", 0)
                evaluated = correct + incorrect

                accuracy = (correct / evaluated * 100) if evaluated > 0 else 0

                project_field_details["agents"][agent_key] = {
                    "correct": correct,
                    "incorrect": incorrect,
                    "skipped": skipped,
                    "evaluated": evaluated,
                    "accuracy": round(accuracy, 1)
                }

        project_details.append(project_field_details)

    return agent_stats, project_details


def print_detailed_report(agent_stats: Dict, project_details: List[Dict]):
    """Print a comprehensive scoring report."""

    print("🏆 THREE-AGENT SCORING REPORT")
    print("=" * 60)

    # Overall scores
    agent_names = {
        "basic_agent": "Basic Agent",
        "function_agent": "Function Agent",
        "expert_agent": "Expert Agent"
    }

    print("\n📊 OVERALL PERFORMANCE")
    print("-" * 40)

    overall_scores = {}

    for agent_key, agent_name in agent_names.items():
        stats = agent_stats[agent_key]
        total_correct = stats["correct"]
        total_incorrect = stats["incorrect"]
        total_skipped = stats["skipped"]
        total_evaluated = total_correct + total_incorrect

        if total_evaluated > 0:
            accuracy = (total_correct / total_evaluated) * 100
            overall_scores[agent_key] = accuracy
        else:
            accuracy = 0
            overall_scores[agent_key] = 0

        print(f"\n🤖 {agent_name}:")
        print(f"   ✅ Correct: {total_correct}")
        print(f"   ❌ Incorrect: {total_incorrect}")
        print(f"   ⏭️ Skipped: {total_skipped}")
        print(f"   📊 Overall Score: {accuracy:.1f}/100")
        print(f"   📈 Projects: {len(set(stats['projects']))}")

    # Ranking
    if overall_scores:
        print(f"\n🏆 AGENT RANKING (by accuracy)")
        print("-" * 40)

        sorted_agents = sorted(overall_scores.items(), key=lambda x: x[1], reverse=True)

        for i, (agent_key, score) in enumerate(sorted_agents, 1):
            agent_name = agent_names[agent_key]
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
            print(f"   {medal} {i}. {agent_name}: {score:.1f}%")

    # Project-by-project breakdown
    if project_details:
        print(f"\n📋 PROJECT-BY-PROJECT BREAKDOWN")
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

                    print(f"   {agent_name}: {accuracy:.1f}% ({correct}/{evaluated})")


def save_scoring_report(agent_stats: Dict, project_details: List[Dict]):
    """Save the scoring report to a JSON file."""

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

        if total_evaluated > 0:
            accuracy = (total_correct / total_evaluated) * 100
        else:
            accuracy = 0

        final_scores[agent_key] = {
            "agent_name": agent_name,
            "correct": total_correct,
            "incorrect": total_incorrect,
            "skipped": stats["skipped"],
            "evaluated": total_evaluated,
            "accuracy": round(accuracy, 1),
            "projects_count": len(set(stats["projects"]))
        }

    # Create report data
    report_data = {
        "report_date": datetime.now().isoformat(),
        "report_type": "three_agent_scoring",
        "overall_scores": final_scores,
        "project_details": project_details,
        "summary": {
            "total_projects": len(project_details),
            "best_agent": max(final_scores.items(), key=lambda x: x[1]["accuracy"])[0] if final_scores else None
        }
    }

    # Save to file
    report_file = "results/scoring_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Detailed report saved to: {report_file}")


def main():
    """Main function to calculate and display scores."""

    print("📊 Three-Agent Scoring Calculator")
    print("=" * 40)

    # Find validation files
    validation_files = find_validation_files()

    if not validation_files:
        print("❌ No three-agent validation files found.")
        print("💡 Run validation first using: python validate_three_agents.py <project_name>")
        return

    print(f"📁 Found {len(validation_files)} validation files")

    # Load all validation data
    all_validation_data = []
    for file_path in validation_files:
        data = load_validation_data(file_path)
        if data:
            all_validation_data.append(data)
            project_name = data.get("project_name", os.path.basename(file_path))
            print(f"   ✅ Loaded: {project_name}")

    if not all_validation_data:
        print("❌ No valid validation data found.")
        return

    # Calculate scores
    print(f"\n🔄 Calculating scores...")
    agent_stats, project_details = calculate_agent_scores(all_validation_data)

    # Print detailed report
    print_detailed_report(agent_stats, project_details)

    # Save report
    save_scoring_report(agent_stats, project_details)

    print(f"\n🏁 Scoring calculation complete!")


if __name__ == "__main__":
    main()
