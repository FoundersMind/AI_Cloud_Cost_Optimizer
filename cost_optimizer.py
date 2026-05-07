# cost_optimizer.py - Main Cost Optimizer Interface
import json
import os
import sys
from typing import Dict, Any, List
from datetime import datetime

from app_paths import ROOT, data_path
from cloud_agents import (
    CLOUD_LABELS,
    CLOUD_PROVIDER_IDS,
    load_selected_cloud_provider,
    normalize_cloud_provider,
    save_cloud_selection,
)
from console_encoding import ensure_utf8_stdio

ensure_utf8_stdio()

class CostOptimizer:
    def __init__(self):
        self.project_description_file = data_path("project_description.txt")
        self.project_profile_file = data_path("project_profile.json")
        self.billing_file = data_path("mock_billing.json")
        self.report_file = data_path("cost_optimization_report.json")
        
    def display_banner(self):
        """Display welcome banner"""
        print("=" * 60)
        print("🚀 MULTI-CLOUD COST OPTIMIZER FOR INTERNS")
        print("=" * 60)
        cc = load_selected_cloud_provider()
        print(f"Active billing agent: {CLOUD_LABELS.get(cc, cc)} (change with menu 0)")
        print("This tool helps you optimize cloud costs by:")
        print("• Analyzing your project's usage on AWS, Azure, or GCP")
        print("• Recommending open-source alternatives")
        print("• Suggesting cost optimization strategies")
        print("• Providing implementation guidance")
        print("=" * 60)

    def get_user_input(self) -> str:
        """Get project description from user"""
        print("\n📝 PROJECT DESCRIPTION INPUT")
        print("-" * 30)
        print("Please describe your project including:")
        print("• What you're building")
        print("• Tech stack (backend, database, storage, etc.)")
        print("• Monthly budget in INR")
        print("• Any specific requirements")
        print("\nExample:")
        print("We are building a real-time employee tracking system.")
        print("Backend is FastAPI in Python, database is PostgreSQL on AWS RDS,")
        print("logs in MongoDB, monitoring via CloudWatch, storage in S3.")
        print("Monthly budget is 20,000 INR, system must guarantee transactional")
        print("consistency and real-time monitoring.")
        print("\n" + "="*50)
        
        description = input("Enter your project description:\n")
        return description.strip()

    def save_project_description(self, description: str):
        """Save project description to file"""
        with open(self.project_description_file, "w", encoding="utf-8") as f:
            f.write(description)
        print(f"✅ Project description saved to {self.project_description_file}")

    def run_step(self, step_name: str, script_name: str):
        """Run a specific step of the cost optimization process"""
        print(f"\n🔄 Running {step_name}...")
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, script_name],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True,
            )
            print(f"✅ {step_name} completed successfully")
            if result.stdout:
                print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"❌ Error in {step_name}: {e}")
            if e.stdout:
                print(f"Output before error:\n{e.stdout}")
            if e.stderr:
                print(f"Error details:\n{e.stderr}")
            return False
        except FileNotFoundError:
            print(f"❌ Script {script_name} not found")
            return False
        return True

    def display_analysis_summary(self):
        """Display cost analysis summary"""
        try:
            with open(self.report_file, "r", encoding="utf-8") as f:
                report = json.load(f)
            
            print("\n📊 COST ANALYSIS RESULTS")
            print("=" * 50)
            
            # Project info
            print(f"Project: {report.get('project_name', 'Unknown')}")
            
            # Cost analysis
            analysis = report.get('analysis', {})
            print(f"Current Monthly Cost: ₹{analysis.get('total_monthly_cost', 0):,.2f}")
            print(f"Budget: ₹{analysis.get('budget', 0):,.2f}")
            
            variance = analysis.get('budget_variance', 0)
            if variance > 0:
                print(f"⚠️  Over Budget by: ₹{variance:,.2f}")
            else:
                print(f"✅ Under Budget by: ₹{abs(variance):,.2f}")
            
            # Summary
            summary = report.get('summary', {})
            print(f"\n💰 OPTIMIZATION OPPORTUNITIES")
            print(f"Total Potential Savings: ₹{summary.get('total_potential_savings', 0):,.2f}")
            print(f"Savings Percentage: {summary.get('savings_percentage', 0):.1f}%")
            print(f"Recommendations Available: {summary.get('recommendations_count', 0)}")
            
            # Top recommendations
            recommendations = report.get('recommendations', [])
            if recommendations:
                print(f"\n🎯 TOP 3 RECOMMENDATIONS:")
                for i, rec in enumerate(recommendations[:3], 1):
                    print(f"\n{i}. {rec.get('title', 'Unknown')}")
                    print(f"   💰 Savings: ₹{rec.get('potential_savings', 0):,.2f}")
                    print(f"   📋 Type: {rec.get('recommendation_type', 'Unknown')}")
                    print(f"   ⚡ Effort: {rec.get('implementation_effort', 'Unknown')}")
                    print(f"   📝 {rec.get('description', 'No description')[:100]}...")
            
        except FileNotFoundError:
            print("❌ Cost analysis report not found. Please run the analysis first.")
        except json.JSONDecodeError:
            print("❌ Error reading cost analysis report.")

    def display_detailed_recommendations(self):
        """Display detailed recommendations"""
        try:
            with open(self.report_file, "r", encoding="utf-8") as f:
                report = json.load(f)
            
            recommendations = report.get('recommendations', [])
            if not recommendations:
                print("❌ No recommendations available.")
                return
            
            print("\n📋 DETAILED RECOMMENDATIONS")
            print("=" * 50)
            
            for i, rec in enumerate(recommendations, 1):
                print(f"\n{i}. {rec.get('title', 'Unknown')}")
                print("-" * 40)
                print(f"Service: {rec.get('service', 'Unknown')}")
                print(f"Current Cost: ₹{rec.get('current_cost', 0):,.2f}")
                print(f"Potential Savings: ₹{rec.get('potential_savings', 0):,.2f}")
                print(f"Type: {rec.get('recommendation_type', 'Unknown')}")
                print(f"Effort: {rec.get('implementation_effort', 'Unknown')}")
                print(f"Risk: {rec.get('risk_level', 'Unknown')}")
                print(f"\nDescription:")
                print(f"{rec.get('description', 'No description')}")
                
                steps = rec.get('steps', [])
                if steps:
                    print(f"\nImplementation Steps:")
                    for j, step in enumerate(steps, 1):
                        print(f"  {j}. {step}")
                print()
                
        except FileNotFoundError:
            print("❌ Cost analysis report not found.")
        except json.JSONDecodeError:
            print("❌ Error reading recommendations.")

    def export_report(self, format_type: str = "json"):
        """Export report in different formats"""
        try:
            with open(self.report_file, "r", encoding="utf-8") as f:
                report = json.load(f)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if format_type.lower() == "json":
                filename = data_path(f"cost_report_{timestamp}.json")
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
                print(f"✅ Report exported to {filename}")
                
            elif format_type.lower() == "txt":
                filename = data_path(f"cost_report_{timestamp}.txt")
                with open(filename, "w", encoding="utf-8") as f:
                    f.write("AWS COST OPTIMIZATION REPORT\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Project: {report.get('project_name', 'Unknown')}\n\n")
                    
                    analysis = report.get('analysis', {})
                    f.write("COST ANALYSIS:\n")
                    f.write(f"Current Monthly Cost: ₹{analysis.get('total_monthly_cost', 0):,.2f}\n")
                    f.write(f"Budget: ₹{analysis.get('budget', 0):,.2f}\n")
                    f.write(f"Budget Variance: ₹{analysis.get('budget_variance', 0):,.2f}\n\n")
                    
                    summary = report.get('summary', {})
                    f.write("OPTIMIZATION SUMMARY:\n")
                    f.write(f"Total Potential Savings: ₹{summary.get('total_potential_savings', 0):,.2f}\n")
                    f.write(f"Savings Percentage: {summary.get('savings_percentage', 0):.1f}%\n\n")
                    
                    recommendations = report.get('recommendations', [])
                    f.write("RECOMMENDATIONS:\n")
                    for i, rec in enumerate(recommendations, 1):
                        f.write(f"\n{i}. {rec.get('title', 'Unknown')}\n")
                        f.write(f"   Savings: ₹{rec.get('potential_savings', 0):,.2f}\n")
                        f.write(f"   Type: {rec.get('recommendation_type', 'Unknown')}\n")
                        f.write(f"   Description: {rec.get('description', 'No description')}\n")
                
                print(f"✅ Report exported to {filename}")
            else:
                print("❌ Unsupported format. Use 'json' or 'txt'")
                
        except FileNotFoundError:
            print("❌ Cost analysis report not found.")
        except Exception as e:
            print(f"❌ Error exporting report: {e}")

    def set_cloud_provider_cli(self) -> None:
        """Pick AWS / Azure / GCP for synthetic billing + analysis agents."""
        print("\n☁️  PRIMARY CLOUD PROVIDER")
        print("-" * 30)
        for i, cid in enumerate(CLOUD_PROVIDER_IDS, 1):
            print(f"  {i}. {CLOUD_LABELS[cid]}")
        raw = input("\nSelect cloud (1-3) or press Enter to keep current: ").strip()
        if not raw:
            print(f"Keeping: {CLOUD_LABELS[load_selected_cloud_provider()]}")
            return
        try:
            n = int(raw)
            if 1 <= n <= len(CLOUD_PROVIDER_IDS):
                save_cloud_selection(CLOUD_PROVIDER_IDS[n - 1])
                print(f"✅ Set to: {CLOUD_LABELS[CLOUD_PROVIDER_IDS[n - 1]]}")
                return
        except ValueError:
            pass
        alt = normalize_cloud_provider(raw)
        save_cloud_selection(alt)
        print(f"✅ Set to: {CLOUD_LABELS.get(alt, alt)}")

    def show_menu(self):
        """Display main menu"""
        while True:
            print("\n🎛️  MAIN MENU")
            print("-" * 20)
            print("0. ☁️  Set primary cloud (AWS / Azure / GCP)")
            print("1. 📝 Enter New Project Description")
            print("2. 🔄 Run Complete Cost Analysis")
            print("3. 📊 View Analysis Summary")
            print("4. 📋 View Detailed Recommendations")
            print("5. 💾 Export Report")
            print("6. ❓ Help")
            print("7. 🚪 Exit")
            
            choice = input("\nSelect an option (0-7): ").strip()
            
            if choice == "0":
                self.set_cloud_provider_cli()
            
            elif choice == "1":
                description = self.get_user_input()
                if description:
                    self.save_project_description(description)
                    print("✅ Project description saved!")
                    
            elif choice == "2":
                print("\n🚀 Running Complete Cost Analysis Pipeline...")
                steps = [
                    ("Project Profile Generation", "generate_profile.py"),
                    ("Billing Data Generation", "generate_billing.py"),
                    ("Cost Analysis", "analyze_billing.py")
                ]
                
                success = True
                for step_name, script_name in steps:
                    if not self.run_step(step_name, script_name):
                        success = False
                        break
                
                if success:
                    print("\n🎉 Cost analysis completed successfully!")
                    self.display_analysis_summary()
                else:
                    print("\n❌ Cost analysis failed. Please check the errors above.")
                    
            elif choice == "3":
                self.display_analysis_summary()
                
            elif choice == "4":
                self.display_detailed_recommendations()
                
            elif choice == "5":
                print("\nExport options:")
                print("1. JSON format")
                print("2. Text format")
                export_choice = input("Select format (1-2): ").strip()
                
                if export_choice == "1":
                    self.export_report("json")
                elif export_choice == "2":
                    self.export_report("txt")
                else:
                    print("❌ Invalid choice")
                    
            elif choice == "6":
                self.show_help()
                
            elif choice == "7":
                print("\n👋 Thank you for using Multi-Cloud Cost Optimizer!")
                break
                
            else:
                print("❌ Invalid choice. Please select 0-7.")

    def show_help(self):
        """Display help information"""
        print("\n❓ HELP - MULTI-CLOUD COST OPTIMIZER")
        print("=" * 40)
        print("This tool helps interns learn cloud cost optimization by:")
        print()
        print("1. 📝 PROJECT DESCRIPTION:")
        print("   - Describe your project, tech stack, and budget")
        print("   - Include cloud services you plan to use")
        print("   - Mention any specific requirements")
        print()
        print("2. 🔄 COST ANALYSIS:")
        print("   - Generates synthetic billing for your selected cloud (menu 0)")
        print("   - Analyzes costs against your budget")
        print("   - Identifies optimization opportunities")
        print()
        print("3. 📊 RECOMMENDATIONS:")
        print("   - Open-source alternatives to paid services")
        print("   - Provider-native optimizations (AWS / Azure / GCP)")
        print("   - Architecture improvements")
        print("   - Implementation guidance")
        print()
        print("4. 💾 EXPORT:")
        print("   - Save reports in JSON or text format")
        print("   - Share with team or mentors")
        print()
        print("💡 TIPS:")
        print("   - Be specific about your tech stack")
        print("   - Include realistic budget expectations")
        print("   - Review all recommendations carefully")
        print("   - Consider implementation effort vs. savings")

def main():
    """Main function"""
    optimizer = CostOptimizer()
    optimizer.display_banner()
    optimizer.show_menu()

if __name__ == "__main__":
    main()
