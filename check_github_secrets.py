#!/usr/bin/env python3
"""
Script to help verify GitHub Actions secrets are configured
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("\n📋 GITHUB SECRETS CHECKLIST")
print("=" * 60)
print("\nYou need to add these secrets to your GitHub repository:")
print("Go to: Settings → Secrets and variables → Actions → New repository secret\n")

secrets_needed = {
    'SUPABASE_URL': os.getenv('SUPABASE_URL', ''),
    'SUPABASE_KEY': os.getenv('SUPABASE_KEY', ''),
    'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', ''),
    'FIRECRAWL_API_KEY': os.getenv('FIRECRAWL_API_KEY', ''),
}

print("Copy and paste these values into GitHub Secrets:\n")
print("-" * 60)

for secret_name, value in secrets_needed.items():
    if value:
        print(f"\n🔑 Secret Name: {secret_name}")
        print(f"   Value: {value}")
        print(f"   Status: ✓ Found in .env")
    else:
        print(f"\n🔑 Secret Name: {secret_name}")
        print(f"   Value: [NOT FOUND IN .ENV]")
        print(f"   Status: ✗ Missing")

print("\n" + "-" * 60)
print("\n📝 INSTRUCTIONS:")
print("1. Go to your GitHub repository")
print("2. Click on 'Settings' tab")
print("3. In the left sidebar, click 'Secrets and variables' → 'Actions'")
print("4. Click 'New repository secret'")
print("5. Add each secret above with its exact name and value")
print("6. After adding all secrets, you can trigger the workflow manually:")
print("   - Go to 'Actions' tab")
print("   - Click on 'AI News Crawler'")
print("   - Click 'Run workflow'")
print("\n✨ The workflow is scheduled to run daily at 9 AM UTC")
print("   You can change this in .github/workflows/crawler.yml\n")