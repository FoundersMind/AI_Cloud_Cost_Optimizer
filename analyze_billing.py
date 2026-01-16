# analyze_billing.py - Cost Analysis and Optimization Engine
import json
import os
from typing import Dict, List, Any
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CostAnalyzer:
    def __init__(self):
        self.HF_TOKEN = os.getenv("HF_TOKEN")
        self.MODEL_ID = "meta-llama/Meta-Llama-3-8B-Instruct"
        self.client = InferenceClient(self.MODEL_ID, token=self.HF_TOKEN)

    def load_project_data(self) -> Dict[str, Any]:
        """Load project profile and billing data"""
        try:
            with open("project_profile.json", "r", encoding="utf-8") as f:
                profile = json.load(f)
            
            with open("mock_billing.json", "r", encoding="utf-8") as f:
                billing = json.load(f)
                
            return {"profile": profile, "billing": billing}
        except FileNotFoundError as e:
            print(f"Error loading data: {e}")
            return None

    def analyze_costs(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze billing data and identify cost optimization opportunities"""
        profile = data["profile"]
        billing = data["billing"]
        
        # Calculate total costs by service
        service_costs = {}
        total_monthly_cost = 0
        
        for record in billing:
            service = record.get("service", "Unknown")
            cost = record.get("cost_inr", 0)
            
            if service not in service_costs:
                service_costs[service] = 0
            service_costs[service] += cost
            total_monthly_cost += cost
        
        # Identify high-cost services
        high_cost_services = {k: v for k, v in service_costs.items() if v > 1000}
        
        # Compare with budget
        budget = profile.get("budget_inr_per_month", 0)
        budget_variance = total_monthly_cost - budget
        
        return {
            "total_monthly_cost": total_monthly_cost,
            "budget": budget,
            "budget_variance": budget_variance,
            "service_costs": service_costs,
            "high_cost_services": high_cost_services,
            "is_over_budget": budget_variance > 0
        }

    def generate_optimization_recommendations(self, analysis: Dict[str, Any], data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate specific cost optimization recommendations using LLM"""
        profile = data["profile"]
        billing = data["billing"]
        
        # LLM-only recommendations
        try:
            messages = [
                {
                    "role": "system",
                    "content": """You are an expert cloud cost optimization consultant with deep knowledge of all major cloud providers (AWS, Azure, GCP, Oracle Cloud, DigitalOcean, etc.) and open-source alternatives. You provide intelligent, data-driven recommendations for reducing cloud costs while maintaining performance and reliability. You consider all cloud providers, free tiers, open-source solutions, and cost optimization strategies."""
                },
                {
                    "role": "user",
                    "content": f"""
Analyze this project's cloud costs and provide intelligent optimization recommendations:

PROJECT PROFILE:
{json.dumps(profile, indent=2)}

CURRENT BILLING ANALYSIS:
{json.dumps(analysis, indent=2)}

BILLING DETAILS:
{json.dumps(billing, indent=2)}

TASK: Provide 6-10 intelligent cost optimization recommendations in JSON format.

REQUIREMENTS for each recommendation:
- title: Clear, actionable title
- service: Which cloud service/provider this applies to
- current_cost: Current monthly cost in INR (from billing data)
- potential_savings: Realistic estimated monthly savings in INR
- recommendation_type: "open_source", "free_tier", "alternative_provider", "optimization", "architecture_change", or "right_sizing"
- description: Detailed explanation with reasoning
- implementation_effort: "low", "medium", or "high"
- risk_level: "low", "medium", or "high"
- steps: Array of 3-5 specific implementation steps
- cloud_providers: Array of relevant cloud providers (AWS, Azure, GCP, etc.)

INTELLIGENT ANALYSIS FOCUS:
1. **Open-source alternatives** to any paid services (PostgreSQL, MongoDB, Redis, etc.)
2. **Free tier opportunities** across all cloud providers
3. **Alternative cloud providers** with better pricing
4. **Architecture optimizations** (serverless, containers, microservices)
5. **Resource right-sizing** based on actual usage patterns
6. **Cost-effective storage solutions** (object storage, CDN, etc.)
7. **Database optimization** strategies
8. **Monitoring and logging** cost reductions
9. **Network and bandwidth** optimizations
10. **Development vs production** environment strategies

CONSIDER:
- Budget constraints and variance
- Project requirements and constraints
- Technology stack compatibility
- Migration complexity and risks
- Long-term cost implications
- Performance impact
- Free tier limits and restrictions

OUTPUT: Only valid JSON array, no explanations or markdown.
"""
                }
            ]
            
            resp = self.client.chat_completion(messages=messages, max_tokens=1500)
            
            # Handle different response formats
            if hasattr(resp, 'choices') and resp.choices:
                raw_output = resp.choices[0].message["content"]
            elif hasattr(resp, 'generated_text'):
                raw_output = resp.generated_text
            else:
                raw_output = str(resp)
            
            print(f"Raw LLM response (preview): {raw_output[:300]}...")
            
            # Clean the response
            cleaned = self._clean_json_response(raw_output)
            print(f"Cleaned response (preview): {cleaned[:300]}...")
            
            if cleaned and cleaned.startswith('['):
                recommendations = json.loads(cleaned)
                print(f"Successfully parsed {len(recommendations)} LLM recommendations")
                return recommendations
            else:
                print("Error: Invalid JSON response from LLM")
                raise ValueError("Invalid JSON response from LLM")
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            raise
    
    def _clean_json_response(self, text: str) -> str:
        """Clean and extract JSON from LLM response"""
        import re
        
        # Remove markdown code blocks
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        
        # Find JSON array
        first_bracket = text.find('[')
        if first_bracket != -1:
            text = text[first_bracket:]
        
        # Find matching closing bracket
        bracket_count = 0
        end_pos = -1
        for i, char in enumerate(text):
            if char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    end_pos = i + 1
                    break
        
        if end_pos != -1:
            text = text[:end_pos]
        
        return text.strip()

    def _get_intelligent_fallback_recommendations(self, analysis: Dict[str, Any], data: Dict[str, Any]) -> List[Dict[str, Any]]:
        raise RuntimeError("Fallback disabled: Relying solely on LLM for recommendations")

    def generate_cost_report(self) -> Dict[str, Any]:
        """Generate comprehensive cost analysis report"""
        data = self.load_project_data()
        if not data:
            return {"error": "Could not load project data"}
        
        analysis = self.analyze_costs(data)
        recommendations = self.generate_optimization_recommendations(analysis, data)
        
        # Calculate total potential savings
        total_potential_savings = sum(rec.get("potential_savings", 0) for rec in recommendations)
        
        report = {
            "project_name": data["profile"].get("name", "Unknown Project"),
            "analysis": analysis,
            "recommendations": recommendations,
            "summary": {
                "total_potential_savings": total_potential_savings,
                "savings_percentage": (total_potential_savings / analysis["total_monthly_cost"] * 100) if analysis["total_monthly_cost"] > 0 else 0,
                "recommendations_count": len(recommendations),
                "high_impact_recommendations": len([r for r in recommendations if r.get("potential_savings", 0) > 1000])
            }
        }
        
        return report

    def save_report(self, report: Dict[str, Any], filename: str = "cost_optimization_report.json"):
        """Save the cost optimization report to file"""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Cost optimization report saved to {filename}")

def main():
    """Main function to run cost analysis"""
    analyzer = CostAnalyzer()
    
    print("Analyzing project costs...")
    report = analyzer.generate_cost_report()
    
    if "error" in report:
        print(f"❌ {report['error']}")
        return
    
    # Save report
    analyzer.save_report(report)
    
    # Print summary
    print("\nCOST ANALYSIS SUMMARY")
    print("=" * 50)
    print(f"Project: {report['project_name']}")
    print(f"Current Monthly Cost (INR): {report['analysis']['total_monthly_cost']:,.2f}")
    print(f"Budget (INR): {report['analysis']['budget']:,.2f}")
    print(f"Budget Variance (INR): {report['analysis']['budget_variance']:,.2f}")
    print(f"Potential Savings (INR): {report['summary']['total_potential_savings']:,.2f}")
    print(f"Savings Percentage: {report['summary']['savings_percentage']:.1f}%")
    print(f"Recommendations: {report['summary']['recommendations_count']}")
    
    if report['analysis']['is_over_budget']:
        print("WARNING: Project is OVER BUDGET!")
    else:
        print("Project is within budget")
    
    print("\nTOP RECOMMENDATIONS:")
    for i, rec in enumerate(report['recommendations'][:3], 1):
        print(f"{i}. {rec['title']}")
        print(f"   Potential Savings (INR): {rec['potential_savings']:,.2f}")
        print(f"   Type: {rec['recommendation_type']}")
        print(f"   Effort: {rec['implementation_effort']}")
        print()

if __name__ == "__main__":
    main()
