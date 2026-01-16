# demo.py - Quick Demo of the Cost Optimizer System
import json
import os

def run_demo():
    """Run a quick demo of the cost optimizer system"""
    print("🚀 AWS COST OPTIMIZER - DEMO")
    print("=" * 40)
    
    # Check if we have the required files
    required_files = [
        "cost_optimizer.py",
        "generate_profile.py", 
        "generate_billing.py",
        "analyze_billing.py",
        "requirements.txt",
        "README.md"
    ]
    
    print("📁 Checking system files...")
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file}")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n⚠️  Missing files: {', '.join(missing_files)}")
        return
    
    print("\n📝 Sample Project Description:")
    sample_description = """We are building a real-time employee tracking system. 
Backend is FastAPI in Python, database is PostgreSQL on AWS RDS, 
logs in MongoDB, monitoring via CloudWatch, storage in S3. 
Monthly budget is 20,000 INR, system must guarantee transactional 
consistency and real-time monitoring."""
    
    print(sample_description)
    
    # Save sample description
    with open("project_description.txt", "w", encoding="utf-8") as f:
        f.write(sample_description)
    print("\n✅ Sample project description saved!")
    
    print("\n🎯 What the system will do:")
    print("1. Extract structured data from project description")
    print("2. Generate synthetic AWS billing data")
    print("3. Analyze costs against budget")
    print("4. Provide optimization recommendations")
    print("5. Suggest open-source alternatives")
    
    print("\n🚀 To run the full system:")
    print("python cost_optimizer.py")
    
    print("\n📊 Expected output includes:")
    print("• Current monthly cost analysis")
    print("• Budget variance (over/under)")
    print("• Top cost optimization recommendations")
    print("• Open-source alternatives to paid services")
    print("• Implementation steps and effort estimates")
    
    print("\n💡 Key learning outcomes:")
    print("• Understanding AWS cost structures")
    print("• Identifying cost optimization opportunities")
    print("• Learning about open-source alternatives")
    print("• Making informed architecture decisions")

if __name__ == "__main__":
    run_demo()
