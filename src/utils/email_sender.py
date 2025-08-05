import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

class EmailSender:
    def __init__(self):
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_user)
        self.from_name = os.getenv('FROM_NAME', 'AI Newsletter')
        
        if not self.smtp_user or not self.smtp_password:
            print("Warning: SMTP credentials not configured. Email sending will be disabled.")
    
    async def send_newsletter(self, subject: str, content: str, recipients: List[str]) -> bool:
        if not self.smtp_user or not self.smtp_password:
            print("Email sending is disabled. Configure SMTP settings to enable.")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            
            html_content = self._markdown_to_html(content)
            
            text_part = MIMEText(content, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                
                for recipient in recipients:
                    msg['To'] = recipient
                    server.send_message(msg)
                    del msg['To']
            
            print(f"Newsletter sent to {len(recipients)} recipients")
            return True
            
        except Exception as e:
            print(f"Failed to send newsletter: {e}")
            return False
    
    def _markdown_to_html(self, markdown: str) -> str:
        html = markdown.replace('\n\n', '</p><p>')
        html = f'<p>{html}</p>'
        
        html = html.replace('**', '<strong>', 1).replace('**', '</strong>', 1)
        while '**' in html:
            html = html.replace('**', '<strong>', 1).replace('**', '</strong>', 1)
        
        lines = html.split('\n')
        formatted_lines = []
        for line in lines:
            if line.strip().startswith('Link:'):
                url = line.replace('Link:', '').strip()
                line = f'Link: <a href="{url}">{url}</a>'
            formatted_lines.append(line)
        html = '\n'.join(formatted_lines)
        
        html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                h1, h2 {{
                    color: #2c3e50;
                }}
                strong {{
                    color: #2c3e50;
                }}
                a {{
                    color: #3498db;
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
                p {{
                    margin-bottom: 15px;
                }}
            </style>
        </head>
        <body>
            {html}
        </body>
        </html>
        """
        
        return html