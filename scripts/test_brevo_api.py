"""
Test Brevo API connection and email sending directly.
This bypasses Flask to isolate configuration issues.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_brevo_api():
    """Test Brevo API with direct SDK calls"""
    print("=" * 60)
    print("BREVO API EMAIL TEST")
    print("=" * 60)
    
    # Check if SDK is installed
    try:
        import sib_api_v3_sdk
        from sib_api_v3_sdk.rest import ApiException
        print("✓ Brevo SDK imported successfully")
    except ImportError as e:
        print(f"✗ ERROR: Brevo SDK not installed: {e}")
        print("\nInstall it with: pip install sib-api-v3-sdk")
        return False
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Get API key
    api_key = os.environ.get('BREVO_API_KEY')
    if not api_key:
        print("✗ ERROR: BREVO_API_KEY not found in environment")
        print("Set it in your .env file:")
        print("BREVO_API_KEY=xkeysib-your-actual-api-key-here")
        return False
    
    # Mask API key for display (show first/last 8 chars)
    masked_key = f"{api_key[:8]}...{api_key[-8:]}" if len(api_key) > 16 else "***"
    print(f"✓ API Key found: {masked_key}")
    
    # Get sender email
    sender_email = os.environ.get('BREVO_SENDER_EMAIL') or os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@teamsobuy.shop'
    print(f"✓ Sender email: {sender_email}")
    
    # Configure Brevo
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = api_key
    
    # Test 1: Get account info
    print("\n" + "=" * 60)
    print("TEST 1: Checking Brevo Account")
    print("=" * 60)
    try:
        api_client = sib_api_v3_sdk.ApiClient(configuration)
        account_api = sib_api_v3_sdk.AccountApi(api_client)
        account_info = account_api.get_account()
        
        print(f"✓ Account Email: {account_info.email}")
        print(f"✓ Company Name: {account_info.company_name}")
        print(f"✓ Plan Type: {account_info.plan[0].type if account_info.plan else 'N/A'}")
        
        # Check email credits
        try:
            if hasattr(account_info, 'plan') and account_info.plan:
                plan = account_info.plan[0]
                if hasattr(plan, 'credits'):
                    print(f"✓ Email Credits: {plan.credits}")
                if hasattr(plan, 'credits_type'):
                    print(f"  Credits Type: {plan.credits_type}")
        except Exception as e:
            print(f"  (Could not fetch credit info: {e})")
            
    except ApiException as e:
        print(f"✗ API Error: {e}")
        print(f"  Status: {e.status}")
        print(f"  Reason: {e.reason}")
        if e.status == 401:
            print("\n⚠ AUTHENTICATION FAILED!")
            print("  Your API key is invalid or expired.")
            print("  Get a new one from: https://app.brevo.com/settings/keys/api")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False
    
    # Test 2: Check sender domains
    print("\n" + "=" * 60)
    print("TEST 2: Checking Sender Domains & Verification")
    print("=" * 60)
    try:
        senders_api = sib_api_v3_sdk.SendersApi(api_client)
        senders = senders_api.get_senders()
        
        if senders and hasattr(senders, 'senders') and senders.senders:
            print(f"✓ Found {len(senders.senders)} verified sender(s):")
            sender_verified = False
            for s in senders.senders:
                status = "✓ VERIFIED" if s.get('active', False) else "✗ NOT VERIFIED"
                print(f"  - {s.get('email', 'N/A')}: {status}")
                if s.get('email') == sender_email and s.get('active', False):
                    sender_verified = True
            
            if not sender_verified:
                print(f"\n⚠ WARNING: Sender email '{sender_email}' is not verified!")
                print("  You must verify your sender email in Brevo dashboard:")
                print("  https://app.brevo.com/settings/senders")
                print("\n  Without verification, emails will be rejected!")
        else:
            print("✗ No senders found in account")
            print("  Add and verify a sender at: https://app.brevo.com/settings/senders")
            
    except ApiException as e:
        print(f"⚠ Could not fetch senders: {e}")
    except Exception as e:
        print(f"⚠ Error checking senders: {e}")
    
    # Test 3: Send test email
    print("\n" + "=" * 60)
    print("TEST 3: Sending Test Email")
    print("=" * 60)
    
    recipient = input("\nEnter recipient email address (or press Enter to skip): ").strip()
    if not recipient:
        print("Skipping email send test.")
        return True
    
    print(f"\nSending test email to: {recipient}")
    print("From: SoBuy <{}>".format(sender_email))
    
    try:
        email_api = sib_api_v3_sdk.TransactionalEmailsApi(api_client)
        
        send_model = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": recipient}],
            sender={"email": sender_email, "name": "SoBuy"},
            subject="Test Email from SoBuy - Brevo API",
            html_content="""
                <html>
                <body>
                    <h2>✓ Success!</h2>
                    <p>This is a test email sent via Brevo API.</p>
                    <p>If you received this, your Brevo configuration is working correctly!</p>
                    <hr>
                    <p style="color: #666; font-size: 12px;">
                        Sent from: SoBuy E-commerce Platform<br>
                        Powered by Brevo Transactional Email API
                    </p>
                </body>
                </html>
            """,
            text_content="Success! This is a test email sent via Brevo API. If you received this, your configuration is working!"
        )
        
        response = email_api.send_transac_email(send_model)
        
        # Extract message ID
        msg_id = getattr(response, 'messageId', None) or getattr(response, 'message_id', None)
        
        print(f"\n✓ Email sent successfully!")
        print(f"  Message ID: {msg_id}")
        print(f"\n  Check the inbox of: {recipient}")
        print(f"  Also check spam/junk folder!")
        print(f"\n  Track delivery in Brevo dashboard:")
        print(f"  https://app.brevo.com/log/transactional")
        
        return True
        
    except ApiException as e:
        print(f"\n✗ EMAIL SEND FAILED!")
        print(f"  Status: {e.status}")
        print(f"  Reason: {e.reason}")
        print(f"  Body: {e.body}")
        
        if e.status == 400:
            print("\n⚠ BAD REQUEST - Common issues:")
            print("  - Sender email not verified")
            print("  - Invalid recipient email format")
            print("  - Missing required fields")
        elif e.status == 401:
            print("\n⚠ AUTHENTICATION ERROR - API key is invalid")
        elif e.status == 402:
            print("\n⚠ PAYMENT REQUIRED - Check your Brevo account credits")
        
        return False
        
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n")
    success = test_brevo_api()
    print("\n" + "=" * 60)
    if success:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ TESTS FAILED - See errors above")
    print("=" * 60)
    print("\n")
