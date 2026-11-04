"""
Quick credential validator — run this before starting the app:
    python check_credentials.py
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("IBM_WATSONX_API_KEY", "")
project_id = os.getenv("IBM_WATSONX_PROJECT_ID", "")
url = os.getenv("IBM_WATSONX_URL", "https://us-south.ml.cloud.ibm.com")

print("=" * 55)
print("  IBM watsonx.ai Credential Check")
print("=" * 55)

errors = []

# 1. API Key length check
print(f"\n[1] API Key length: {len(api_key)} chars", end="  ")
if len(api_key) == 44:
    print("✓ CORRECT")
elif len(api_key) == 0:
    print("✗ MISSING")
    errors.append("IBM_WATSONX_API_KEY is empty in .env")
else:
    print(f"✗ WRONG (expected 44, got {len(api_key)}) — key is truncated or invalid")
    errors.append(f"IBM_WATSONX_API_KEY must be 44 chars (yours is {len(api_key)})")

# 2. Project ID format check
import re
print(f"\n[2] Project ID: {project_id[:8]}...", end="  ")
uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
if uuid_pattern.match(project_id):
    print("✓ Valid UUID format")
elif not project_id:
    print("✗ MISSING")
    errors.append("IBM_WATSONX_PROJECT_ID is empty in .env")
else:
    print("✗ Invalid format (should be a UUID like xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)")
    errors.append("IBM_WATSONX_PROJECT_ID format looks wrong")

# 3. URL check
print(f"\n[3] URL: {url}", end="  ")
if url.startswith("https://") and "ml.cloud.ibm.com" in url:
    print("✓ CORRECT")
else:
    print("✗ Unexpected URL format")
    errors.append(f"IBM_WATSONX_URL looks wrong: {url}")

# 4. Live IAM token test
print("\n[4] Testing IBM IAM authentication...", end="  ", flush=True)
try:
    import httpx
    resp = httpx.post(
        "https://iam.cloud.ibm.com/identity/token",
        data={"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": api_key},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    if resp.status_code == 200:
        print("✓ API key is VALID — IAM token obtained")
    elif resp.status_code == 400:
        body = resp.json()
        code = body.get("errorCode", "")
        msg = body.get("errorMessage", "")
        print(f"✗ REJECTED — {code}: {msg}")
        errors.append(f"API key rejected by IBM IAM: {msg}")
    else:
        print(f"✗ Unexpected status {resp.status_code}: {resp.text[:200]}")
        errors.append(f"IAM returned HTTP {resp.status_code}")
except Exception as e:
    print(f"✗ Network error: {e}")
    errors.append(f"Could not reach IBM IAM: {e}")

print("\n" + "=" * 55)
if errors:
    print("  RESULT: FAILED — fix these issues:")
    for err in errors:
        print(f"    • {err}")
    print("\n  Get a new API key at: https://cloud.ibm.com/iam/apikeys")
    sys.exit(1)
else:
    print("  RESULT: ALL CHECKS PASSED ✓")
    print("  Your credentials look good — start the app with: python app.py")
print("=" * 55)
