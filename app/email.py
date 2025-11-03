import ssl
import smtplib
from email.message import EmailMessage
from threading import Thread
from flask import current_app


def _send_async_email(app, msg: EmailMessage):
    with app.app_context():
        cfg = app.config
        server = cfg.get('MAIL_SERVER')
        # support implicit SSL (SMTPS) or STARTTLS depending on config
        use_ssl = bool(cfg.get('MAIL_USE_SSL', False))
        use_tls = bool(cfg.get('MAIL_USE_TLS', True))
        # default ports: 465 for SSL, 587 for TLS
        default_port = 465 if use_ssl else 587
        port = int(cfg.get('MAIL_PORT', default_port))
        username = cfg.get('MAIL_USERNAME')
        password = cfg.get('MAIL_PASSWORD')

        context = ssl.create_default_context()
        try:
            if not server:
                app.logger.error('MAIL_SERVER is empty')
                return
            if use_ssl:
                # use SMTP_SSL with host/port passed to constructor to ensure proper SNI
                with smtplib.SMTP_SSL(host=server, port=port, context=context, timeout=20) as smtp:
                    if app.debug:
                        smtp.set_debuglevel(1)
                    if username and password:
                        smtp.login(username, password)
                    smtp.send_message(msg)
            else:
                # connect via plain SMTP then optionally STARTTLS
                with smtplib.SMTP(host=server, port=port, timeout=20) as smtp:
                    if app.debug:
                        smtp.set_debuglevel(1)
                    if use_tls:
                        smtp.starttls(context=context)
                    if username and password:
                        smtp.login(username, password)
                    smtp.send_message(msg)
        except Exception as e:
            app.logger.exception('Failed to send email: %s', e)


def send_email(subject, recipients, text_body, html_body=None):
    app = current_app._get_current_object()
    cfg = app.config
    sender = cfg.get('MAIL_DEFAULT_SENDER') or cfg.get('MAIL_USERNAME')

    if isinstance(recipients, str):
        recipients = [r.strip() for r in recipients.split(',') if r.strip()]

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    msg.set_content(text_body or '')

    if html_body:
        msg.add_alternative(html_body, subtype='html')

    thr = Thread(target=_send_async_email, args=(app, msg), daemon=True)
    thr.start()


def send_otp(email, otp_code, username=None, expires=None):
    subject = 'Your SoBuy OTP'
    from flask import render_template
    text = render_template('email/otp.txt', otp=otp_code, username=username, expires=expires)
    html = render_template('email/otp.html', otp=otp_code, username=username, expires=expires)
    send_email(subject, email, text, html)
