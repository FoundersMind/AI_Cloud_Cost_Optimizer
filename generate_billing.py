# generate_billing.py - Generate synthetic AWS billing data with error handling
import json
import os
import re
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

import sys

from app_paths import data_path
from console_encoding import ensure_utf8_stdio

ensure_utf8_stdio()
from groq_llm import chat_completion
from industry_playbooks import load_selected_industry_id, playbook_prompt_block

# Load .env file
load_dotenv(data_path(".env"))

def clean_json_response(text):
    """Clean and extract JSON from LLM response"""
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

try:
    with open(data_path("project_profile.json"), "r", encoding="utf-8") as f:
        profile = json.load(f)

    industry_id = load_selected_industry_id()
    industry_block = playbook_prompt_block(industry_id)

    print("Generating synthetic cloud billing data...")
    
    # LLM-only generation
    try:
        messages = [
            {
                "role": "system",
                "content": """You are an expert cloud billing analyst who generates realistic, comprehensive billing data for cloud projects. You understand all major cloud providers (AWS, Azure, GCP, Oracle Cloud, DigitalOcean, etc.) and create detailed, realistic billing scenarios that reflect actual production usage patterns."""
            },
            {
                "role": "user",
                "content": f"""
Generate comprehensive, realistic cloud billing data for this project:

PROJECT PROFILE:
{json.dumps(profile, indent=2)}

INDUSTRY_CONTEXT (bias cost drivers & service mix toward this vertical):
{industry_block}

REQUIREMENTS:
- Generate 12-20 realistic billing records
- Each record must include ALL these fields:
  - month: Current month (e.g., "2025-01")
  - service: Cloud service name (EC2, RDS, S3, Lambda, CloudWatch, etc.)
  - resource_id: Realistic resource identifier (e.g., "i-ecommerce-web-01", "db-prod-mysql")
  - region: AWS region (e.g., "ap-south-1", "us-east-1")
  - usage_type: Specific usage type (e.g., "Linux/UNIX (on-demand)", "Storage:Standard")
  - usage_quantity: Realistic usage number
  - unit: Appropriate unit (hours, GB, requests, etc.)
  - cost_inr: Realistic cost in INR based on budget allocation
  - desc: Detailed description of what this resource does

BILLING DISTRIBUTION GUIDELINES:
- Compute (EC2/Lambda): 40-50% of budget
- Database (RDS): 20-25% of budget  
- Storage (S3): 10-15% of budget
- Network (CloudFront, ELB): 8-12% of budget
- Monitoring (CloudWatch): 5-8% of budget
- Other services: 5-10% of budget

REALISTIC SCENARIOS TO INCLUDE:
- Multiple EC2 instances (web, API, dev environments)
- Database instances with backups
- Multiple S3 buckets (uploads, backups, logs)
- Lambda functions for different purposes
- CloudWatch logs and metrics
- Load balancers and CDN
- DNS, email, and notification services
- Development and staging environments
- Where the vertical implies it (e.g., retail: CDN/edge-heavy; fintech: egress + KMS; healthcare: storage + audit logs), overweight those line items modestly but keep totals plausible vs budget.

TOTAL BUDGET: ₹{profile.get('budget_inr_per_month', 20000):,}

OUTPUT: Only valid JSON array, no explanations or markdown.
"""
            }
        ]
        
        raw_output = chat_completion(messages, max_tokens=2000, temperature=0.25)

        print(f"Raw LLM response (preview): {raw_output[:300]}...")
        
        # Clean the response
        cleaned = clean_json_response(raw_output)
        print(f"Cleaned response (preview): {cleaned[:300]}...")
        
        if cleaned and cleaned.startswith('['):
            billing = json.loads(cleaned)
            print(f"Successfully parsed {len(billing)} LLM billing records")
            if len(billing) < 5:
                print("Error: LLM generated too few billing records")
                sys.exit(1)
        else:
            print("Error: Invalid JSON response from LLM")
            sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during billing generation: {e}")
        sys.exit(1)
    
    # Validate billing data
    if not isinstance(billing, list):
        print("Error: Billing is not a JSON array")
        sys.exit(1)
    
    # Ensure we have at least some billing data
    if len(billing) == 0:
        print("Error: Empty billing data")
        sys.exit(1)
    
    # Validate each record
    for record in billing:
        if not isinstance(record, dict):
            continue
        # Ensure required fields
        if 'month' not in record:
            record['month'] = datetime.now().strftime("%Y-%m")
        if 'cost_inr' not in record:
            record['cost_inr'] = random.randint(500, 5000)
    
    # Save billing data
    with open(data_path("mock_billing.json"), "w", encoding="utf-8") as f:
        json.dump(billing, f, indent=2, ensure_ascii=False)
    
    print("Billing data saved to mock_billing.json")
    print("Generated Billing Data Preview:")
    print(json.dumps(billing[:2], indent=2, ensure_ascii=False))
    
    # Calculate total cost
    total_cost = sum(record.get('cost_inr', 0) for record in billing)
    print(f"Total Monthly Cost (INR): {total_cost:,}")
    
except FileNotFoundError:
    print("Error: project_profile.json not found. Run generate_profile.py first.")
    sys.exit(1)
except Exception as e:
    print(f"Unexpected error: {e}")
    sys.exit(1)
