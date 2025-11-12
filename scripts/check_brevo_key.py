"""
Quick script to check Brevo API key configuration
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("BREVO API KEY CONFIGURATION CHECK")
print("=" * 60)

# Check if .env file exists
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(env_path):
    print(f"✓ .env file found at: {env_path}")
else:
    print(f"✗ .env file NOT found at: {env_path}")
    print("  Create it by copying .env.template and filling in real values")

# Get API key from environment
api_key = os.environ.get('BREVO_API_KEY')

if not api_key:
    print("\n✗ BREVO_API_KEY is NOT SET in environment!")
    print("\nTO FIX:")
    print("1. Go to: https://app.brevo.com/settings/keys/api")
    print("2. Create a new API key (or copy existing one)")
    print("3. Add it to your .env file:")
    print("   BREVO_API_KEY=xkeysib-your-actual-key-here")
    print("4. Restart your Flask application")
else:
    # Mask the key for security (show first 12 and last 8 chars)
    if len(api_key) > 20:
        masked = f"{api_key[:12]}...{api_key[-8:]}"
    else:
        masked = "***"
    
    print(f"\n✓ BREVO_API_KEY is set")
    print(f"  Value: {masked}")
    print(f"  Length: {len(api_key)} characters")
    
    # Check if it looks like a valid Brevo key
    if api_key.startswith('xkeysib-'):
        print("  ✓ Format looks correct (starts with 'xkeysib-')")
    else:
        print("  ✗ WARNING: Key doesn't start with 'xkeysib-'")
        print("    This doesn't look like a valid Brevo API key!")

# Check other email settings
print("\n" + "=" * 60)
print("OTHER EMAIL SETTINGS")
print("=" * 60)

mail_provider = os.environ.get('MAIL_PROVIDER', 'brevo')
print(f"MAIL_PROVIDER: {mail_provider}")

mail_default_sender = os.environ.get('MAIL_DEFAULT_SENDER')
print(f"MAIL_DEFAULT_SENDER: {mail_default_sender or 'NOT SET'}")

brevo_sender = os.environ.get('BREVO_SENDER_EMAIL')
print(f"BREVO_SENDER_EMAIL: {brevo_sender or 'NOT SET'}")

print("\n" + "=" * 60)
print("NEXT STEPS:")
print("=" * 60)
print("1. Get your API key from: https://app.brevo.com/settings/keys/api")
print("2. Update .env file with the correct key")
print("3. Restart your Flask app")
print("4. Run the test_brevo_api.py script to verify")
print("=" * 60)
