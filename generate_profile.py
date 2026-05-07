# generate_profile.py (fixed for LLaMA 3 with error handling)
import json
import re
from dotenv import load_dotenv

import sys

from app_paths import data_path
from console_encoding import ensure_utf8_stdio

ensure_utf8_stdio()

from groq_llm import chat_completion
from cloud_agents import load_selected_cloud_provider, normalize_cloud_provider

load_dotenv(data_path(".env"))

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
    with open(data_path("project_description.txt"), "r", encoding="utf-8") as f:
        desc_text = f.read().strip()

    selected_cloud = load_selected_cloud_provider()
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

User-selected primary cloud (use this value unless the description clearly contradicts with a different single cloud):
"{selected_cloud}"  → must be one of: "aws", "azure", "gcp"

Fields to extract:
- name (short project name)
- budget_inr_per_month (extract number from description)
- primary_cloud_provider (string: exactly one of aws, azure, gcp — prefer "{selected_cloud}" when ambiguous)
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
    
    raw_output = chat_completion(messages, max_tokens=600, temperature=0.2)

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
    required_keys = [
        "name",
        "budget_inr_per_month",
        "primary_cloud_provider",
        "description",
        "tech_stack",
        "non_functional_requirements",
    ]
    for k in required_keys:
        if k not in profile:
            print(f"Error: Missing required key in profile: {k}")
            sys.exit(1)

    profile["primary_cloud_provider"] = normalize_cloud_provider(
        profile.get("primary_cloud_provider") or selected_cloud
    )

    # Save profile
    with open(data_path("project_profile.json"), "w", encoding="utf-8") as f:
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
