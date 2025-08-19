#!/usr/bin/env python3
"""
Calculate confusion matrix metrics by comparing human-judged vs LLM-judged scoring reports.
This script computes overall confusion matrix metrics across all agents combined.
"""

import os
import json
from typing import Dict, List, Tuple
from datetime import datetime


def load_scoring_reports():
    """Load both human and LLM scoring reports."""
    
    human_report_file = "results/scoring_report.json"
    llm_report_file = "results/scoring_report_llm.json"
    
    if not os.path.exists(human_report_file):
        print(f"❌ Human scoring report not found: {human_report_file}")
        print("💡 Run human validation first: python validate_three_agents.py")
        return None, None
    
    if not os.path.exists(llm_report_file):
        print(f"❌ LLM scoring report not found: {llm_report_file}")
        print("💡 Run LLM evaluation first: python llm_judge.py")
        return None, None
    
    try:
        with open(human_report_file, 'r', encoding='utf-8') as f:
            human_data = json.load(f)
        
        with open(llm_report_file, 'r', encoding='utf-8') as f:
            llm_data = json.load(f)
        
        print(f"✅ Loaded human scoring report: {human_report_file}")
        print(f"✅ Loaded LLM scoring report: {llm_report_file}")
        
        return human_data, llm_data
        
    except Exception as e:
        print(f"❌ Error loading reports: {e}")
        return None, None


def calculate_overall_confusion_matrix(human_data: Dict, llm_data: Dict) -> Tuple[Dict, List[Dict]]:
    """
    Calculate overall confusion matrix metrics across all agents combined.
    
    This aggregates the confusion matrix across all three agents to give
    a general view of how well the LLM judge performs overall.
    """
    
    # Initialize overall confusion matrix
    overall_confusion = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
    
    project_details = []
    
    # Create lookup for human project data
    human_projects = {}
    for project in human_data.get("project_details", []):
        human_projects[project["project_name"]] = project
    
    # Process each LLM project
    for llm_project in llm_data.get("project_details", []):
        project_name = llm_project["project_name"]
        
        if project_name not in human_projects:
            print(f"⚠️ Project {project_name} not found in human validation, skipping")
            continue
        
        human_project = human_projects[project_name]
        project_confusion = {
            "project_name": project_name,
            "overall_metrics": {"tp": 0, "fp": 0, "tn": 0, "fn": 0},
            "agent_breakdown": {}
        }
        
        # Aggregate metrics across all agents for this project
        project_tp = 0
        project_fp = 0
        project_tn = 0
        project_fn = 0
        
        # Compare each agent's performance
        for agent_key in ["basic_agent", "function_agent", "expert_agent"]:
            if agent_key in llm_project["agents"] and agent_key in human_project["agents"]:
                llm_agent = llm_project["agents"][agent_key]
                human_agent = human_project["agents"][agent_key]
                
                # Get field-level evaluations
                llm_correct = llm_agent.get("correct", 0)
                llm_incorrect = llm_agent.get("incorrect", 0)
                human_correct = human_agent.get("correct", 0)
                human_incorrect = human_agent.get("incorrect", 0)
                
                # Calculate confusion matrix for this agent/project
                agent_confusion = calculate_agent_confusion(
                    llm_correct, llm_incorrect, 
                    human_correct, human_incorrect
                )
                
                # Add to project breakdown
                project_confusion["agent_breakdown"][agent_key] = agent_confusion
                
                # Aggregate to project level
                project_tp += agent_confusion["tp"]
                project_fp += agent_confusion["fp"]
                project_tn += agent_confusion["tn"]
                project_fn += agent_confusion["fn"]
        
        # Store project-level aggregated metrics
        project_confusion["overall_metrics"] = {
            "tp": project_tp,
            "fp": project_fp,
            "tn": project_tn,
            "fn": project_fn,
            "total": project_tp + project_fp + project_tn + project_fn
        }
        
        # Add to overall confusion matrix
        overall_confusion["tp"] += project_tp
        overall_confusion["fp"] += project_fp
        overall_confusion["tn"] += project_tn
        overall_confusion["fn"] += project_fn
        
        project_details.append(project_confusion)
    
    return overall_confusion, project_details


def calculate_agent_confusion(llm_correct: int, llm_incorrect: int, 
                            human_correct: int, human_incorrect: int) -> Dict:
    """
    Calculate confusion matrix metrics for a single agent/project combination.
    
    This is an approximation since we don't have field-level mapping between
    human and LLM evaluations. We estimate the confusion matrix based on
    the differences in correct/incorrect counts.
    """
    
    total_fields = llm_correct + llm_incorrect
    
    if total_fields == 0:
        return {"tp": 0, "fp": 0, "tn": 0, "fn": 0, "total": 0}
    
    # Estimate confusion matrix
    # This is a simplified approach - for exact metrics we'd need field-level data
    
    # Calculate metrics based on the assumption that differences represent misclassifications
    tp = min(llm_correct, human_correct)  # Both say correct
    tn = min(llm_incorrect, human_incorrect)  # Both say incorrect
    
    # Remaining fields represent disagreements
    remaining_correct = llm_correct - tp
    remaining_incorrect = llm_incorrect - tn
    
    # Distribute remaining fields as FP and FN
    fp = remaining_correct  # LLM says correct, Human says incorrect
    fn = remaining_incorrect  # LLM says incorrect, Human says correct
    
    return {
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "total": total_fields,
        "llm_correct": llm_correct,
        "llm_incorrect": llm_incorrect,
        "human_correct": human_correct,
        "human_incorrect": human_incorrect
    }


def calculate_overall_rates(confusion_matrix: Dict) -> Dict:
    """Calculate overall performance rates from the combined confusion matrix."""
    
    tp = confusion_matrix["tp"]
    fp = confusion_matrix["fp"]
    tn = confusion_matrix["tn"]
    fn = confusion_matrix["fn"]
    
    # Calculate rates
    total_positive = tp + fn  # Human says correct
    total_negative = fp + tn  # Human says incorrect
    
    # False Positive Rate (FPR) = FP / (FP + TN)
    fpr = (fp / (fp + tn)) if (fp + tn) > 0 else 0
    
    # False Negative Rate (FNR) = FN / (TP + FN)
    fnr = (fn / (tp + fn)) if (tp + fn) > 0 else 0
    
    # True Positive Rate (TPR) = TP / (TP + FN) = Sensitivity = Recall
    tpr = (tp / (tp + fn)) if (tp + fn) > 0 else 0
    
    # True Negative Rate (TNR) = TN / (FP + TN) = Specificity
    tnr = (tn / (fp + tn)) if (fp + tn) > 0 else 0
    
    # Precision = TP / (TP + FP)
    precision = (tp / (tp + fp)) if (tp + fp) > 0 else 0
    
    # F1 Score = 2 * (Precision * Recall) / (Precision + Recall)
    f1_score = (2 * precision * tpr / (precision + tpr)) if (precision + tpr) > 0 else 0
    
    # Overall accuracy = (TP + TN) / (TP + FP + TN + FN)
    accuracy = (tp + tn) / (tp + fp + tn + fn) if (tp + fp + tn + fn) > 0 else 0
    
    return {
        "confusion_matrix": confusion_matrix,
        "rates": {
            "false_positive_rate": round(fpr, 4),
            "false_negative_rate": round(fnr, 4),
            "true_positive_rate": round(tpr, 4),
            "true_negative_rate": round(tnr, 4),
            "precision": round(precision, 4),
            "recall": round(tpr, 4),
            "f1_score": round(f1_score, 4),
            "accuracy": round(accuracy, 4)
        }
    }


def print_overall_confusion_matrix_report(confusion_matrix: Dict, rates: Dict):
    """Print the overall confusion matrix report."""
    
    print("🔍 OVERALL CONFUSION MATRIX ANALYSIS: LLM vs Human Validation")
    print("=" * 70)
    print("📊 Aggregated across all agents (Basic, Function, Expert)")
    print("=" * 70)
    
    cm = confusion_matrix
    rate_data = rates["rates"]
    
    # Print confusion matrix
    print("\n📊 Overall Confusion Matrix:")
    print(f"   True Positives (TP):  {cm['tp']:4d} | Human ✓, LLM ✓")
    print(f"   False Positives (FP): {cm['fp']:4d} | Human ✗, LLM ✓")
    print(f"   True Negatives (TN):  {cm['tn']:4d} | Human ✗, LLM ✗")
    print(f"   False Negatives (FN): {cm['fn']:4d} | Human ✓, LLM ✗")
    
    total = cm['tp'] + cm['fp'] + cm['tn'] + cm['fn']
    print(f"   Total Evaluations:    {total:4d}")
    
    # Print rates
    print(f"\n📈 Overall Performance Metrics:")
    print(f"   Accuracy:     {rate_data['accuracy']:.3f}")
    print(f"   Precision:    {rate_data['precision']:.3f}")
    print(f"   Recall:       {rate_data['recall']:.3f}")
    print(f"   F1 Score:     {rate_data['f1_score']:.3f}")
    print(f"   FPR:          {rate_data['false_positive_rate']:.3f}")
    print(f"   FNR:          {rate_data['false_negative_rate']:.3f}")
    print(f"   TPR:          {rate_data['true_positive_rate']:.3f}")
    print(f"   TNR:          {rate_data['true_negative_rate']:.3f}")
    
    # Print summary statistics
    print(f"\n📋 Summary:")
    print(f"   Total Correctly Classified: {cm['tp'] + cm['tn']:,} fields")
    print(f"   Total Misclassified:       {cm['fp'] + cm['fn']:,} fields")
    print(f"   Overall Error Rate:        {((cm['fp'] + cm['fn']) / total * 100):.1f}%")


def save_overall_confusion_matrix_report(confusion_matrix: Dict, rates: Dict, project_details: List[Dict]):
    """Save the overall confusion matrix report to a JSON file."""
    
    # Create results directory if it doesn't exist
    os.makedirs("results", exist_ok=True)
    
    # Create report data
    report_data = {
        "report_date": datetime.now().isoformat(),
        "report_type": "overall_confusion_matrix_llm_vs_human",
        "description": "Overall confusion matrix metrics comparing LLM judge vs human validation across all agents",
        "overall_confusion_matrix": confusion_matrix,
        "overall_performance_metrics": rates,
        "project_details": project_details,
        "summary": {
            "total_projects": len(project_details),
            "total_evaluations": confusion_matrix["tp"] + confusion_matrix["fp"] + confusion_matrix["tn"] + confusion_matrix["fn"],
            "metrics_calculated": ["accuracy", "precision", "recall", "f1_score", "fpr", "fnr", "tpr", "tnr"],
            "note": "Metrics are aggregated across all three agents (Basic, Function, Expert)"
        }
    }
    
    # Save to file
    output_file = "results/llm_judge_confusion_matrix_report.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Overall confusion matrix report saved to: {output_file}")
    
    return output_file


def main():
    """Main function to calculate overall confusion matrix metrics."""
    
    print("🔍 Overall LLM vs Human Validation Confusion Matrix Calculator")
    print("=" * 70)
    
    # Load scoring reports
    human_data, llm_data = load_scoring_reports()
    
    if not human_data or not llm_data:
        print("❌ Failed to load required reports. Exiting.")
        return
    
    print(f"\n📊 Human validation summary:")
    print(f"   Total projects: {human_data.get('summary', {}).get('total_projects', 0)}")
    print(f"   Best agent: {human_data.get('summary', {}).get('best_agent', 'unknown')}")
    
    print(f"\n🤖 LLM evaluation summary:")
    print(f"   Total projects: {llm_data.get('summary', {}).get('total_projects', 0)}")
    print(f"   LLM model: {llm_data.get('llm_model', 'unknown')}")
    print(f"   Best agent: {llm_data.get('summary', {}).get('best_agent', 'unknown')}")
    
    # Calculate overall confusion matrix
    print(f"\n🔄 Calculating overall confusion matrix metrics...")
    confusion_matrix, project_details = calculate_overall_confusion_matrix(human_data, llm_data)
    
    # Calculate overall rates
    rates = calculate_overall_rates(confusion_matrix)
    
    # Print report
    print_overall_confusion_matrix_report(confusion_matrix, rates)
    
    # Save report
    output_file = save_overall_confusion_matrix_report(confusion_matrix, rates, project_details)
    
    print(f"\n🏁 Overall confusion matrix analysis complete!")
    print(f"📁 Results saved to: {output_file}")


if __name__ == "__main__":
    main()
