import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
from flask import current_app

def send_async_email(app, msg):
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
            app.logger.info(f"E-mail succesvol verzonden naar {msg['To']}")
        except Exception as e:
            app.logger.error(f"Fout bij verzenden e-mail naar {msg['To']}: {e}")

def send_email(to, subject, html_content):
    app = current_app._get_current_object()
    
    sender = app.config.get('MAIL_DEFAULT_SENDER') or app.config.get('MAIL_USERNAME')
    if not sender:
        app.logger.warning("Geen MAIL_DEFAULT_SENDER of MAIL_USERNAME ingesteld. E-mail is niet verzonden.")
        return
        
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"Sponsoring De Kampanje <{sender}>"
    msg['To'] = to
    
    part = MIMEText(html_content, 'html', 'utf-8')
    msg.attach(part)
    
    # Send email in a background thread to prevent blocking the Flask request
    threading.Thread(target=send_async_email, args=(app, msg)).start()
