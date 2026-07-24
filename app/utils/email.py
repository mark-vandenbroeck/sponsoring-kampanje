import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
import requests
from flask import current_app

def send_async_email_via_http(app, to, subject, html_content, sender, api_key):
    with app.app_context():
        try:
            url = "https://api.brevo.com/v3/smtp/email"
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "api-key": api_key
            }
            payload = {
                "sender": {
                    "name": "Sponsoring De Kampanje",
                    "email": sender
                },
                "to": [
                    {
                        "email": to
                    }
                ],
                "subject": subject,
                "htmlContent": html_content
            }
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code in (200, 201, 202):
                app.logger.info(f"E-mail succesvol verzonden via Brevo HTTP API naar {to}")
            else:
                app.logger.error(f"Fout bij verzenden via Brevo HTTP API naar {to}: {response.status_code} - {response.text}")
        except Exception as e:
            app.logger.error(f"Fout bij HTTP API-aanroep naar Brevo voor {to}: {e}")

def send_async_email_via_smtp(app, msg):
    with app.app_context():
        try:
            # Connect to SMTP server using config
            mail_server = app.config.get('MAIL_SERVER')
            mail_port_val = app.config.get('MAIL_PORT')
            mail_username = app.config.get('MAIL_USERNAME')
            mail_password = app.config.get('MAIL_PASSWORD')
            mail_use_ssl = app.config.get('MAIL_USE_SSL', True)
            
            if not mail_server or not mail_username or not mail_password:
                app.logger.warning("SMTP-configuratie ontbreekt (MAIL_SERVER, MAIL_USERNAME of MAIL_PASSWORD). E-mail is niet verzonden.")
                return
                
            try:
                mail_port = int(mail_port_val)
            except (TypeError, ValueError):
                mail_port = 465 if mail_use_ssl else 587
                
            if mail_use_ssl:
                server = smtplib.SMTP_SSL(mail_server, mail_port, timeout=10)
            else:
                server = smtplib.SMTP(mail_server, mail_port, timeout=10)
                server.starttls()
                
            server.login(mail_username, mail_password)
            server.send_message(msg)
            server.quit()
            app.logger.info(f"E-mail succesvol verzonden via SMTP naar {msg['To']}")
        except Exception as e:
            app.logger.error(f"Fout bij verzenden e-mail via SMTP naar {msg['To']}: {e}")

def send_email(to, subject, html_content):
    app = current_app._get_current_object()
    
    sender = app.config.get('MAIL_DEFAULT_SENDER') or app.config.get('MAIL_USERNAME')
    if not sender:
        app.logger.warning("Geen MAIL_DEFAULT_SENDER of MAIL_USERNAME ingesteld. E-mail is niet verzonden.")
        return
        
    api_key = app.config.get('BREVO_API_KEY')
    if api_key:
        # Use Brevo HTTP API (ideal for cloud platforms like Render that block SMTP ports)
        threading.Thread(target=send_async_email_via_http, args=(app, to, subject, html_content, sender, api_key)).start()
    else:
        # Fallback to standard SMTP (ideal for local development)
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"Sponsoring De Kampanje <{sender}>"
        msg['To'] = to
        
        part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(part)
        
        threading.Thread(target=send_async_email_via_smtp, args=(app, msg)).start()
