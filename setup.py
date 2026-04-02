# setup.py - Installation script for AWS Cost Optimizer
import subprocess
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app_paths import data_path

def install_requirements():
    """Install required packages"""
    print("📦 Installing required packages...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", data_path("requirements.txt")]
        )
        print("✅ All packages installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing packages: {e}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} is not compatible")
        print("Please use Python 3.8 or higher")
        return False

def create_sample_files():
    """Create sample files if they don't exist"""
    print("📝 Creating sample files...")
    
    # Create sample project description if it doesn't exist
    if not os.path.exists(data_path("project_description.txt")):
        sample_desc = """We are building a real-time employee tracking system. 
Backend is FastAPI in Python, database is PostgreSQL on AWS RDS, 
logs in MongoDB, monitoring via CloudWatch, storage in S3. 
Monthly budget is 20,000 INR, system must guarantee transactional 
consistency and real-time monitoring."""
        
        with open(data_path("project_description.txt"), "w", encoding="utf-8") as f:
            f.write(sample_desc)
        print("✅ Created sample project_description.txt")
    
    # Create .env file template if it doesn't exist
    if not os.path.exists(data_path(".env")):
        env_template = """# AI Cloud Cost Optimizer — environment variables
# Groq API key: https://console.groq.com/keys
GROQ_API_KEY=

# Optional: Groq model id (default: llama-3.3-70b-versatile)
# GROQ_MODEL=llama-3.1-8b-instant
"""
        with open(data_path(".env"), "w", encoding="utf-8") as f:
            f.write(env_template)
        print("✅ Created .env template file")

def main():
    """Main setup function"""
    print("🚀 AWS COST OPTIMIZER - SETUP")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        return
    
    # Install requirements
    if not install_requirements():
        return
    
    # Create sample files
    create_sample_files()
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Run the demo: python demo.py")
    print("2. Start the cost optimizer: python cost_optimizer.py")
    print("3. Read the documentation: README.md")
    
    print("\n💡 Tips:")
    print("• The system uses synthetic data for learning purposes")
    print("• All recommendations are suggestions - evaluate them carefully")
    print("• Focus on understanding cost optimization concepts")
    
    print("\n🆘 Need help? Check README.md for detailed instructions")

if __name__ == "__main__":
    main()
