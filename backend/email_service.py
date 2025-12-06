"""
Serviço de envio de emails
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional
import json

class EmailService:
    """Serviço para envio de emails"""
    
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_from = os.getenv("SMTP_FROM", self.smtp_user)
        self.use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    
    def is_configured(self) -> bool:
        """Verifica se o serviço de email está configurado"""
        return bool(self.smtp_user and self.smtp_password)
    
    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        attachments: Optional[List[dict]] = None
    ) -> bool:
        """
        Envia email
        
        Args:
            to_emails: Lista de emails destinatários
            subject: Assunto do email
            body_html: Corpo do email em HTML
            body_text: Corpo do email em texto (opcional)
            attachments: Lista de anexos [{"filename": "nome.pdf", "content": bytes, "content_type": "application/pdf"}]
        
        Returns:
            True se enviado com sucesso, False caso contrário
        """
        if not self.is_configured():
            print("⚠️ Serviço de email não configurado. Configure SMTP_USER e SMTP_PASSWORD")
            return False
        
        try:
            # Cria mensagem
            msg = MIMEMultipart('alternative')
            msg['From'] = self.smtp_from
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            # Adiciona corpo do email
            if body_text:
                part_text = MIMEText(body_text, 'plain', 'utf-8')
                msg.attach(part_text)
            
            part_html = MIMEText(body_html, 'html', 'utf-8')
            msg.attach(part_html)
            
            # Adiciona anexos
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['content'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment["filename"]}'
                    )
                    msg.attach(part)
            
            # Envia email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            return True
        
        except Exception as e:
            print(f"❌ Erro ao enviar email: {e}")
            return False
    
    def send_report_email(
        self,
        to_emails: List[str],
        client_name: str,
        report_name: str,
        periodo: str,
        attachments: Optional[List[dict]] = None
    ) -> bool:
        """Envia email com relatório"""
        subject = f"Relatório de Absenteísmo - {client_name} - {periodo}"
        
        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #1a237e; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Relatório de Absenteísmo</h1>
                </div>
                <div class="content">
                    <p>Olá,</p>
                    <p>Segue em anexo o <strong>{report_name}</strong> da empresa <strong>{client_name}</strong>.</p>
                    <p><strong>Período:</strong> {periodo}</p>
                    <p>Este é um relatório automático gerado pelo sistema AbsenteismoController.</p>
                </div>
                <div class="footer">
                    <p>AbsenteismoController - GrupoBiomed</p>
                    <p>Este é um email automático, por favor não responda.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        body_text = f"""
        Relatório de Absenteísmo
        
        Olá,
        
        Segue em anexo o {report_name} da empresa {client_name}.
        
        Período: {periodo}
        
        Este é um relatório automático gerado pelo sistema AbsenteismoController.
        
        AbsenteismoController - GrupoBiomed
        """
        
        return self.send_email(to_emails, subject, body_html, body_text, attachments)
    
    def send_alert_email(
        self,
        to_emails: List[str],
        client_name: str,
        alert_title: str,
        alert_message: str,
        alert_severity: str = "medium"
    ) -> bool:
        """Envia email de alerta"""
        severity_colors = {
            "low": "#2196F3",
            "medium": "#FF9800",
            "high": "#F44336",
            "critical": "#B71C1C"
        }
        severity_names = {
            "low": "Baixa",
            "medium": "Média",
            "high": "Alta",
            "critical": "Crítica"
        }
        
        color = severity_colors.get(alert_severity, "#FF9800")
        severity_name = severity_names.get(alert_severity, "Média")
        
        subject = f"⚠️ Alerta: {alert_title} - {client_name}"
        
        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: {color}; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .alert-box {{ background: white; border-left: 4px solid {color}; padding: 15px; margin: 15px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⚠️ Alerta de Absenteísmo</h1>
                </div>
                <div class="content">
                    <p>Olá,</p>
                    <div class="alert-box">
                        <h2 style="margin-top: 0; color: {color};">{alert_title}</h2>
                        <p><strong>Empresa:</strong> {client_name}</p>
                        <p><strong>Severidade:</strong> {severity_name}</p>
                        <p>{alert_message}</p>
                    </div>
                    <p>Acesse o sistema para mais detalhes.</p>
                </div>
                <div class="footer">
                    <p>AbsenteismoController - GrupoBiomed</p>
                    <p>Este é um email automático, por favor não responda.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        body_text = f"""
        Alerta de Absenteísmo
        
        Olá,
        
        {alert_title}
        
        Empresa: {client_name}
        Severidade: {severity_name}
        
        {alert_message}
        
        Acesse o sistema para mais detalhes.
        
        AbsenteismoController - GrupoBiomed
        """
        
        return self.send_email(to_emails, subject, body_html, body_text)

