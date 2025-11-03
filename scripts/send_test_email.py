import os
import ssl
import smtplib
from email.message import EmailMessage

# Simple SMTP test script that reads SMTP config from environment variables.
# Usage:
#   set env vars (see README below) and run:
#   python scripts/send_test_email.py recipient@example.com

RECIPIENT = None
import sys
if len(sys.argv) >= 2:
    RECIPIENT = sys.argv[1]
else:
    print('Usage: python scripts/send_test_email.py recipient@example.com')
    sys.exit(1)

MAIL_SERVER = (os.environ.get('MAIL_SERVER') or '').strip()
MAIL_PORT = os.environ.get('MAIL_PORT')
MAIL_USERNAME = (os.environ.get('MAIL_USERNAME') or '').strip()
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'true').lower() in ('1', 'true', 'yes')
MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'false').lower() in ('1', 'true', 'yes')
MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or MAIL_USERNAME

if not MAIL_SERVER or not MAIL_USERNAME or not MAIL_PASSWORD:
    print('Missing MAIL_SERVER, MAIL_USERNAME or MAIL_PASSWORD environment variables.')
    sys.exit(2)

port = int(MAIL_PORT) if MAIL_PORT else (465 if MAIL_USE_SSL else 587)

msg = EmailMessage()
msg['Subject'] = 'SoBuy SMTP Test'
msg['From'] = MAIL_DEFAULT_SENDER
msg['To'] = RECIPIENT
msg.set_content('This is a test email sent from the SoBuy SMTP test script.')

context = ssl.create_default_context()

print(f"Connecting to {MAIL_SERVER}:{port} (ssl={MAIL_USE_SSL}, tls={MAIL_USE_TLS})")
try:
    if not MAIL_SERVER:
        print('MAIL_SERVER is empty; please set the MAIL_SERVER environment variable')
        sys.exit(2)
    if MAIL_USE_SSL:
        print(f'Connecting (SSL) to {MAIL_SERVER}:{port}')
        with smtplib.SMTP_SSL(host=MAIL_SERVER, port=port, context=context, timeout=20) as smtp:
            smtp.set_debuglevel(1)
            smtp.login(MAIL_USERNAME, MAIL_PASSWORD)
            smtp.send_message(msg)
    else:
        print(f'Connecting (plain) to {MAIL_SERVER}:{port}')
        with smtplib.SMTP(host=MAIL_SERVER, port=port, timeout=20) as smtp:
            if MAIL_USE_TLS:
                smtp.starttls(context=context)
            smtp.set_debuglevel(1)
            smtp.login(MAIL_USERNAME, MAIL_PASSWORD)
            smtp.send_message(msg)
    print('Test email sent successfully to', RECIPIENT)
except Exception as e:
    print('Failed to send test email:', e)
    raise
