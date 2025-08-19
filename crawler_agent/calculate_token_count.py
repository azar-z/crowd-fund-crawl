import os
import json
from vertexai.preview import tokenization
from datetime import datetime

from crawler_agent.agents import ExpertAgent


def compare_token_count():
    """Compare token counts between basic HTML and expert cleaned HTML for all projects."""
    
    single_samples_dir = "single_samples"
    result_file = "results/token_comparison.json"
    
    # Create results directory if it doesn't exist
    os.makedirs("results", exist_ok=True)
    
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
    
    print(f"📁 Found {len(project_names)} projects for token count comparison")
    print("🔄 Starting token count analysis...")
    
    # Initialize token count statistics
    token_stats = {
        "basic_agent": {
            "total_tokens": 0,
            "project_count": 0,
            "projects": []
        },
        "expert_agent": {
            "total_tokens": 0,
            "project_count": 0,
            "projects": []
        }
    }
    
    project_details = []
    
    # Process each project
    for i, project_name in enumerate(project_names, 1):
        print(f"  📋 Processing {i}/{len(project_names)}: {project_name}")
        
        try:
            html_file = os.path.join(single_samples_dir, f"{project_name}.html")
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            model_name = "gemini-1.5-flash-002"
            tokenizer = tokenization.get_tokenizer_for_model(model_name)
            
            # Count tokens for basic HTML
            basic_token_count = tokenizer.count_tokens(html_content).total_tokens
            
            # Count tokens for expert cleaned HTML
            cleaned_html_content = ExpertAgent(api_key="123")._clean_html_efficiently(html_content)
            expert_token_count = tokenizer.count_tokens(cleaned_html_content).total_tokens
            
            # Calculate token reduction
            token_reduction = basic_token_count - expert_token_count
            reduction_percentage = (token_reduction / basic_token_count * 100) if basic_token_count > 0 else 0
            
            # Store project details
            project_data = {
                "project_name": project_name,
                "basic_token_count": basic_token_count,
                "expert_token_count": expert_token_count,
                "token_reduction": token_reduction,
                "reduction_percentage": round(reduction_percentage, 2),
                "processing_date": datetime.now().isoformat()
            }
            project_details.append(project_data)
            
            # Update overall statistics
            token_stats["basic_agent"]["total_tokens"] += basic_token_count
            token_stats["basic_agent"]["project_count"] += 1
            token_stats["basic_agent"]["projects"].append({
                "name": project_name,
                "token_count": basic_token_count
            })
            
            token_stats["expert_agent"]["total_tokens"] += expert_token_count
            token_stats["expert_agent"]["project_count"] += 1
            token_stats["expert_agent"]["projects"].append({
                "name": project_name,
                "token_count": expert_token_count
            })
            
            print(f"    ✅ Basic: {basic_token_count:,} tokens | Expert: {expert_token_count:,} tokens | Reduction: {reduction_percentage:.1f}%")
            
        except Exception as e:
            print(f"    ❌ Error processing {project_name}: {e}")
            continue
    
    # Calculate overall statistics
    if token_stats["basic_agent"]["project_count"] > 0:
        basic_mean = token_stats["basic_agent"]["total_tokens"] / token_stats["basic_agent"]["project_count"]
        token_stats["basic_agent"]["mean_tokens"] = round(basic_mean, 2)
    
    if token_stats["expert_agent"]["project_count"] > 0:
        expert_mean = token_stats["expert_agent"]["total_tokens"] / token_stats["expert_agent"]["project_count"]
        token_stats["expert_agent"]["mean_tokens"] = round(expert_mean, 2)
    
    # Calculate overall token reduction
    total_reduction = token_stats["basic_agent"]["total_tokens"] - token_stats["expert_agent"]["total_tokens"]
    overall_reduction_percentage = (total_reduction / token_stats["basic_agent"]["total_tokens"] * 100) if token_stats["basic_agent"]["total_tokens"] > 0 else 0
    
    # Create final report
    report_data = {
        "report_date": datetime.now().isoformat(),
        "report_type": "token_count_comparison",
        "total_projects": len(project_names),
        "successful_projects": len(project_details),
        "overall_summary": {
            "total_basic_tokens": token_stats["basic_agent"]["total_tokens"],
            "total_expert_tokens": token_stats["expert_agent"]["total_tokens"],
            "total_token_reduction": total_reduction,
            "overall_reduction_percentage": round(overall_reduction_percentage, 2)
        },
        "agent_statistics": {
            "basic_agent": {
                "total_tokens": token_stats["basic_agent"]["total_tokens"],
                "mean_tokens": token_stats["basic_agent"].get("mean_tokens", 0),
                "project_count": token_stats["basic_agent"]["project_count"],
                "projects": token_stats["basic_agent"]["projects"]
            },
            "expert_agent": {
                "total_tokens": token_stats["expert_agent"]["total_tokens"],
                "mean_tokens": token_stats["expert_agent"].get("mean_tokens", 0),
                "project_count": token_stats["expert_agent"]["project_count"],
                "projects": token_stats["expert_agent"]["projects"]
            }
        },
        "project_details": project_details
    }
    
    # Save report to file
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"\n{'='*60}")
    print("📊 TOKEN COUNT COMPARISON SUMMARY")
    print(f"{'='*60}")
    print(f"📁 Total projects analyzed: {len(project_names)}")
    print(f"✅ Successful projects: {len(project_details)}")
    print(f"\n🔢 OVERALL TOKEN COUNTS:")
    print(f"   📄 Basic Agent (raw HTML): {token_stats['basic_agent']['total_tokens']:,} tokens")
    print(f"   🧹 Expert Agent (cleaned): {token_stats['expert_agent']['total_tokens']:,} tokens")
    print(f"   💾 Total reduction: {total_reduction:,} tokens ({overall_reduction_percentage:.1f}%)")
    print(f"\n📊 MEAN TOKENS PER PROJECT:")
    print(f"   📄 Basic Agent: {token_stats['basic_agent'].get('mean_tokens', 0):,.0f} tokens")
    print(f"   🧹 Expert Agent: {token_stats['expert_agent'].get('mean_tokens', 0):,.0f} tokens")
    print(f"\n💾 Detailed report saved to: {result_file}")
    
    return report_data


if __name__ == "__main__":
    compare_token_count()
