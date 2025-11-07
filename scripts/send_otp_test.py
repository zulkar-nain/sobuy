#!/usr/bin/env python3
"""Simple helper to test OTP sending via configured provider (Brevo or SMTP).

Usage:
  python scripts/send_otp_test.py recipient@example.com [OTP] [username]

This script loads the Flask app (create_app) so it uses your app config and env vars.
It does not write any secrets to disk. Make sure your env (or .env file referenced by systemd) contains
BREVO_API_KEY or the MAIL_* settings for SMTP.
"""
import sys
import os

from app import create_app


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/send_otp_test.py recipient@example.com [OTP] [username]")
        sys.exit(1)

    recipient = sys.argv[1]
    otp = sys.argv[2] if len(sys.argv) >= 3 else "123456"
    username = sys.argv[3] if len(sys.argv) >= 4 else None

    # Create the app and send the OTP inside app context
    app = create_app()
    with app.app_context():
        from app.email import send_otp
        print(f"Sending OTP {otp} to {recipient} using configured provider...")
        send_otp(recipient, otp, username=username)
        print("OTP send task queued. Check your inbox and app logs for delivery status.")


if __name__ == '__main__':
    main()
