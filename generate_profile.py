# generate_profile.py (fixed for LLaMA 3 with error handling)
import json
import os
import re
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
MODEL_ID = "meta-llama/Meta-Llama-3-8B-Instruct"

import sys

def clean_json_response(text):
    """Clean and extract JSON from LLM response"""
    # Remove markdown code blocks
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    
    # Remove any text before the first {
    first_brace = text.find('{')
    if first_brace != -1:
        text = text[first_brace:]
    
    # Remove any text after the last }
    last_brace = text.rfind('}')
    if last_brace != -1:
        text = text[:last_brace + 1]
    
    return text.strip()

try:
    client = InferenceClient(MODEL_ID, token=HF_TOKEN)
    
    with open("project_description.txt", "r", encoding="utf-8") as f:
        desc_text = f.read().strip()
    
    print("Generating project profile...")
    
    messages = [
            {
                "role": "system",
                "content": "You are an AI that extracts structured JSON from raw project descriptions. Always respond with valid JSON only."
            },
            {
                "role": "user",
                "content": f"""
Convert the following project description into valid JSON.

Project Description:
{desc_text}

Fields to extract:
- name (short project name)
- budget_inr_per_month (extract number from description)
- description (original description)
- tech_stack (object with categories like backend, database, monitoring, storage)
- non_functional_requirements (array of keywords like scalability, real_time, cost_optimization)

Rules:
- Output ONLY valid JSON, no explanations or markdown
- Extract budget number from text
- Identify tech stack components
- Return valid JSON object
"""
            }
        ]
    
    resp = client.chat_completion(messages=messages, max_tokens=600)
    
    # Handle different response formats
    if hasattr(resp, 'choices') and resp.choices:
        raw_output = resp.choices[0].message["content"]
    elif hasattr(resp, 'generated_text'):
        raw_output = resp.generated_text
    else:
        raw_output = str(resp)
    
    print(f"Raw LLM response (preview): {raw_output[:200]}...")
    
    # Clean the response
    cleaned = clean_json_response(raw_output)
    print(f"Cleaned response (preview): {cleaned[:200]}...")
    
    if cleaned and cleaned.startswith('{'):
        profile = json.loads(cleaned)
        print("Successfully parsed LLM response")
    else:
        print("Error: Invalid JSON response from LLM")
        sys.exit(1)
    
    # Basic validation
    if not isinstance(profile, dict):
        print("Error: Parsed profile is not a JSON object")
        sys.exit(1)
    
    # Ensure required fields exist
    required_keys = ["name", "budget_inr_per_month", "description", "tech_stack", "non_functional_requirements"]
    for k in required_keys:
        if k not in profile:
            print(f"Error: Missing required key in profile: {k}")
            sys.exit(1)
    
    # Save profile
    with open("project_profile.json", "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)
    
    print("Project profile saved to project_profile.json")
    print("Generated Profile:")
    print(json.dumps(profile, indent=2, ensure_ascii=False))
    
except FileNotFoundError:
    print("Error: project_description.txt not found")
    print("Please run the cost optimizer and enter a project description first")
except Exception as e:
    print(f"Unexpected error: {e}")
    sys.exit(1)
