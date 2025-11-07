import os
from threading import Thread
from flask import current_app


def _send_via_brevo(app, subject, sender, recipients, text_body, html_body=None):
    """Send email using Brevo (Sendinblue) Transactional Emails API only."""
    try:
        import sib_api_v3_sdk
        from sib_api_v3_sdk.rest import ApiException
    except Exception:
        app.logger.exception('Brevo SDK not installed or import failed')
        return

    api_key = app.config.get('BREVO_API_KEY') or os.environ.get('BREVO_API_KEY')
    if not api_key:
        app.logger.error('BREVO_API_KEY is not set')
        return

    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = api_key

    api_client = sib_api_v3_sdk.ApiClient(configuration)
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(api_client)

    # parse sender into dict
    sender_email = None
    sender_name = None
    if isinstance(sender, dict):
        sender_email = sender.get('email')
        sender_name = sender.get('name')
    elif isinstance(sender, str):
        if '<' in sender and '>' in sender:
            parts = sender.split('<')
            sender_name = parts[0].strip().strip('"')
            sender_email = parts[1].strip().strip('>')
        else:
            sender_email = sender

    if not sender_email:
        sender_email = app.config.get('MAIL_DEFAULT_SENDER') or app.config.get('MAIL_USERNAME')

    to_list = []
    for r in recipients:
        to_list.append({"email": r})

    send_model = sib_api_v3_sdk.SendSmtpEmail(
        to=to_list,
        sender={"email": sender_email, "name": sender_name} if sender_name else {"email": sender_email},
        subject=subject,
        html_content=html_body,
        text_content=text_body,
    )

    try:
        api_response = api_instance.send_transac_email(send_model)
        # log Brevo response for debugging
        try:
            msg_id = getattr(api_response, 'messageId', None) or getattr(api_response, 'message_id', None)
            app.logger.info('Brevo send_transac_email response, message id: %s', msg_id)
        except Exception:
            app.logger.info('Brevo send_transac_email response: %s', api_response)
    except ApiException as e:
        app.logger.exception('Failed to send email via Brevo: %s', e)
    except Exception as e:
        app.logger.exception('Unexpected error sending email via Brevo: %s', e)


def _send_async_email(app, subject, sender, recipients, text_body, html_body=None):
    with app.app_context():
        _send_via_brevo(app, subject, sender, recipients, text_body, html_body)


def send_email(subject, recipients, text_body, html_body=None):
    app = current_app._get_current_object()
    cfg = app.config
    sender = cfg.get('MAIL_DEFAULT_SENDER') or cfg.get('MAIL_USERNAME')

    if isinstance(recipients, str):
        recipients = [r.strip() for r in recipients.split(',') if r.strip()]

    thr = Thread(target=_send_async_email, args=(app, subject, sender, recipients, text_body, html_body), daemon=True)
    thr.start()


def send_otp(email, otp_code, username=None, expires=None):
    subject = 'Your SoBuy OTP'
    from flask import render_template
    text = render_template('email/otp.txt', otp=otp_code, username=username, expires=expires)
    html = render_template('email/otp.html', otp=otp_code, username=username, expires=expires)
    send_email(subject, email, text, html)
