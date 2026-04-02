# analyze_billing.py - Cost Analysis and Optimization Engine
import json
import os
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

from app_paths import data_path
from console_encoding import ensure_utf8_stdio
from groq_llm import chat_completion
from industry_playbooks import (
    get_playbook,
    load_selected_industry_id,
    playbook_prompt_block,
)

ensure_utf8_stdio()

# Load environment variables
load_dotenv(data_path(".env"))

_RECOMMENDATION_TYPES = frozenset(
    {
        "open_source",
        "free_tier",
        "alternative_provider",
        "optimization",
        "architecture_change",
        "right_sizing",
        "commitment_discount",
        "workload_placement",
        "observability_efficiency",
        "governance_tagging",
    }
)


class CostAnalyzer:
    def load_project_data(self) -> Optional[Dict[str, Any]]:
        """Load project profile and billing data"""
        try:
            with open(data_path("project_profile.json"), "r", encoding="utf-8") as f:
                profile = json.load(f)

            with open(data_path("mock_billing.json"), "r", encoding="utf-8") as f:
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

    def _normalize_recommendation(self, rec: Any, analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not isinstance(rec, dict):
            return None
        title = rec.get("title") or rec.get("name") or "Optimization initiative"
        svc = rec.get("service") or "Multiple services"
        try:
            current_cost = float(rec.get("current_cost", 0) or 0)
        except (TypeError, ValueError):
            current_cost = 0.0
        try:
            potential_savings = float(rec.get("potential_savings", 0) or 0)
        except (TypeError, ValueError):
            potential_savings = 0.0
        rtype = rec.get("recommendation_type") or "optimization"
        if rtype not in _RECOMMENDATION_TYPES:
            rtype = "optimization"
        desc = rec.get("description") or rec.get("summary") or ""
        effort = rec.get("implementation_effort") or "medium"
        if effort not in ("low", "medium", "high"):
            effort = "medium"
        risk = rec.get("risk_level") or "medium"
        if risk not in ("low", "medium", "high"):
            risk = "medium"
        steps = rec.get("steps")
        if not isinstance(steps, list):
            steps = []
        steps = [str(s) for s in steps if s][:8]
        providers = rec.get("cloud_providers")
        if not isinstance(providers, list):
            providers = []
        providers = [str(p) for p in providers if p][:6]
        strategic_theme = rec.get("strategic_theme") or "workload_efficiency"
        finops_practice = rec.get("finops_practice") or "optimize_usage"
        business_kpi_hint = rec.get("business_kpi_hint") or ""

        return {
            "title": str(title)[:200],
            "service": str(svc)[:120],
            "current_cost": round(current_cost, 2),
            "potential_savings": round(max(potential_savings, 0), 2),
            "recommendation_type": rtype,
            "description": str(desc)[:4000],
            "implementation_effort": effort,
            "risk_level": risk,
            "steps": steps,
            "cloud_providers": providers or ["AWS"],
            "strategic_theme": str(strategic_theme)[:120],
            "finops_practice": str(finops_practice)[:120],
            "business_kpi_hint": str(business_kpi_hint)[:240],
        }

    def generate_optimization_recommendations(self, analysis: Dict[str, Any], data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate specific cost optimization recommendations using LLM"""
        profile = data["profile"]
        billing = data["billing"]
        industry_id = load_selected_industry_id()
        industry_block = playbook_prompt_block(industry_id)

        # LLM-only recommendations
        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a principal FinOps + cloud economics advisor for Global 2000 enterprises. "
                        "You align technical cost moves with measurable business KPIs, guardrails (latency, "
                        "availability, compliance), and pragmatic execution (backlog, owners, proof metrics). "
                        "You know AWS/Azure/GCP economics: commitments (Savings Plans, CUD, RIs), spot/spot-like "
                        "for fault-tolerant work, rightsizing, autoscaling, storage lifecycle & tiering, "
                        "data egress controls, observability cardinality, tagging & chargeback, sandbox controls, "
                        "and architectural choices (managed vs self-run). Prefer actionable initiatives over generic advice."
                    ),
                },
                {
                    "role": "user",
                    "content": f"""
Analyze this organization's cloud spend and produce an ENTERPRISE-GRADE savings backlog.

INDUSTRY_CONTEXT:
{industry_block}

PROJECT PROFILE:
{json.dumps(profile, indent=2)}

QUANTITATIVE ANALYSIS:
{json.dumps(analysis, indent=2)}

BILLING LINE ITEMS:
{json.dumps(billing, indent=2)}

TASK: Return 8-12 recommendations as a JSON array. Each item must be a JSON object with EXACT keys:
- title (string)
- service (string)
- current_cost (number, INR/month, grounded in billing where possible; estimate only if needed)
- potential_savings (number INR/month; conservative but meaningful)
- recommendation_type (one of: open_source, free_tier, alternative_provider, optimization, architecture_change, right_sizing, commitment_discount, workload_placement, observability_efficiency, governance_tagging)
- strategic_theme (short string: e.g. "commitments_and_discounts", "workload_efficiency", "data_platform", "observability_tax", "egress_and_network", "governance_chargeback")
- finops_practice (short string mapped to FinOps capabilities language: understand_usage, optimize_usage, quantify_business_value, manage_variability, manage_commitments, etc.)
- business_kpi_hint (string: which business KPI this improves — unit cost, margin, latency risk, auditability, time-to-market)
- description (string: why this saves money, trade-offs, and how to validate with metrics)
- implementation_effort ("low"|"medium"|"high")
- risk_level ("low"|"medium"|"high")
- steps (array of 3-6 concrete steps; include a measurement/validation step)
- cloud_providers (array of strings)

Rules:
1) Respect INDUSTRY compliance/latency constraints — do not suggest shortcuts that break PCI/HIPAA-style boundaries if the vertical implies them.
2) At least 2 items should target enterprise FinOps mechanics (tagging/chargeback anomaly detection, commitment coverage vs baseline, sandbox controls) when plausible.
3) At least 2 items should be observability/storage/network efficiency if billing suggests logs, metrics, S3, or data transfer.
4) Tie savings to billing SKUs where possible (name the service from line items).

OUTPUT: JSON array ONLY, no markdown or commentary.
""",
                },
            ]

            raw_output = chat_completion(messages, max_tokens=2400, temperature=0.25)

            print(f"Raw LLM response (preview): {raw_output[:300]}...")
            
            # Clean the response
            cleaned = self._clean_json_response(raw_output)
            print(f"Cleaned response (preview): {cleaned[:300]}...")
            
            if cleaned and cleaned.startswith('['):
                raw_recs = json.loads(cleaned)
                normalized: List[Dict[str, Any]] = []
                for item in raw_recs:
                    norm = self._normalize_recommendation(item, analysis)
                    if norm:
                        normalized.append(norm)
                print(f"Successfully parsed {len(normalized)} LLM recommendations")
                return normalized
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

        industry_id = load_selected_industry_id()
        ind = get_playbook(industry_id)

        # Calculate total potential savings
        total_potential_savings = sum(rec.get("potential_savings", 0) for rec in recommendations)

        report = {
            "project_name": data["profile"].get("name", "Unknown Project"),
            "meta": {
                "industry_vertical_id": industry_id,
                "industry_label": ind.get("label", industry_id),
                "generator": "analyze_billing.CostAnalyzer",
            },
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
        out = data_path(filename) if not os.path.isabs(filename) else filename
        with open(out, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Cost optimization report saved to {out}")

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
