"""
Sistema de agendamento e envio de relatórios automáticos
"""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
from .models import ReportSchedule, Client
from .email_service import EmailService
from .analytics import Analytics
from .report_generator import ReportGenerator
import json
import os

class ReportScheduler:
    """Gerenciador de relatórios automáticos"""
    
    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailService()
    
    def process_scheduled_reports(self) -> List[dict]:
        """
        Processa todos os relatórios agendados que devem ser enviados agora
        
        Returns:
            Lista de relatórios processados
        """
        now = datetime.now()
        results = []
        
        # Busca relatórios ativos que devem ser enviados
        schedules = self.db.query(ReportSchedule).filter(
            ReportSchedule.is_active == True
        ).all()
        
        for schedule in schedules:
            if self._should_send_now(schedule, now):
                try:
                    result = self._generate_and_send_report(schedule)
                    results.append(result)
                except Exception as e:
                    print(f"Erro ao processar relatório {schedule.id}: {e}")
                    results.append({
                        "schedule_id": schedule.id,
                        "success": False,
                        "error": str(e)
                    })
        
        return results
    
    def _should_send_now(self, schedule: ReportSchedule, now: datetime) -> bool:
        """Verifica se o relatório deve ser enviado agora"""
        # Se já foi enviado hoje, não envia novamente
        if schedule.ultimo_envio:
            if schedule.ultimo_envio.date() == now.date():
                return False
        
        # Verifica frequência
        if schedule.frequencia == "daily":
            # Envia todo dia no horário configurado
            hora_envio = datetime.strptime(schedule.hora_envio, "%H:%M").time()
            return now.time() >= hora_envio
        
        elif schedule.frequencia == "weekly":
            # Envia no dia da semana e horário configurados
            if now.weekday() == schedule.dia_semana:
                hora_envio = datetime.strptime(schedule.hora_envio, "%H:%M").time()
                return now.time() >= hora_envio
            return False
        
        elif schedule.frequencia == "monthly":
            # Envia no dia do mês e horário configurados
            if now.day == schedule.dia_mes:
                hora_envio = datetime.strptime(schedule.hora_envio, "%H:%M").time()
                return now.time() >= hora_envio
            return False
        
        return False
    
    def _generate_and_send_report(self, schedule: ReportSchedule) -> dict:
        """Gera e envia relatório"""
        client = self.db.query(Client).filter(Client.id == schedule.client_id).first()
        if not client:
            raise Exception(f"Cliente {schedule.client_id} não encontrado")
        
        # Calcula período
        periodo_info = self._calculate_period(schedule)
        
        # Gera relatório
        report_files = []
        
        if schedule.formato in ["excel", "ambos"]:
            excel_file = self._generate_excel_report(schedule, periodo_info)
            if excel_file:
                report_files.append(excel_file)
        
        if schedule.formato in ["pdf", "ambos"]:
            pdf_file = self._generate_pdf_report(schedule, periodo_info)
            if pdf_file:
                report_files.append(pdf_file)
        
        # Envia email
        emails = json.loads(schedule.emails_destinatarios) if schedule.emails_destinatarios else []
        if not emails:
            emails = [client.email] if client.email else []
        
        periodo_str = f"{periodo_info['mes_inicio']} a {periodo_info['mes_fim']}"
        
        success = self.email_service.send_report_email(
            to_emails=emails,
            client_name=client.nome_fantasia or client.nome,
            report_name=schedule.nome,
            periodo=periodo_str,
            attachments=report_files
        )
        
        # Atualiza schedule
        schedule.ultimo_envio = datetime.now()
        schedule.proximo_envio = self._calculate_next_send(schedule)
        self.db.commit()
        
        return {
            "schedule_id": schedule.id,
            "success": success,
            "emails_sent": emails,
            "files_generated": len(report_files)
        }
    
    def _calculate_period(self, schedule: ReportSchedule) -> dict:
        """Calcula período do relatório"""
        hoje = datetime.now()
        
        if schedule.periodo == "ultimo_mes":
            mes_fim = hoje.strftime("%Y-%m")
            mes_anterior = (hoje - timedelta(days=32)).replace(day=1)
            mes_inicio = mes_anterior.strftime("%Y-%m")
        elif schedule.periodo == "ultimos_3_meses":
            mes_fim = hoje.strftime("%Y-%m")
            mes_inicio = (hoje - timedelta(days=90)).strftime("%Y-%m")
        elif schedule.periodo == "custom":
            mes_inicio = schedule.mes_inicio_custom
            mes_fim = schedule.mes_fim_custom
        else:
            mes_inicio = hoje.strftime("%Y-%m")
            mes_fim = hoje.strftime("%Y-%m")
        
        return {
            "mes_inicio": mes_inicio,
            "mes_fim": mes_fim
        }
    
    def _generate_excel_report(self, schedule: ReportSchedule, periodo: dict) -> Optional[dict]:
        """Gera relatório em Excel"""
        try:
            # Usa ReportGenerator se disponível
            if ReportGenerator:
                generator = ReportGenerator(self.db)
                file_path = generator.generate_excel_report(
                    client_id=schedule.client_id,
                    mes_inicio=periodo["mes_inicio"],
                    mes_fim=periodo["mes_fim"]
                )
                
                if file_path and os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    
                    filename = f"relatorio_{schedule.client_id}_{periodo['mes_inicio']}_{periodo['mes_fim']}.xlsx"
                    return {
                        "filename": filename,
                        "content": content,
                        "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    }
        except Exception as e:
            print(f"Erro ao gerar Excel: {e}")
        
        return None
    
    def _generate_pdf_report(self, schedule: ReportSchedule, periodo: dict) -> Optional[dict]:
        """Gera relatório em PDF"""
        # PDF ainda não implementado completamente
        # Retorna None por enquanto
        return None
    
    def _calculate_next_send(self, schedule: ReportSchedule) -> datetime:
        """Calcula próxima data de envio"""
        now = datetime.now()
        hora_envio = datetime.strptime(schedule.hora_envio, "%H:%M").time()
        
        if schedule.frequencia == "daily":
            next_date = now + timedelta(days=1)
        elif schedule.frequencia == "weekly":
            days_ahead = schedule.dia_semana - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_date = now + timedelta(days=days_ahead)
        elif schedule.frequencia == "monthly":
            # Próximo mês, mesmo dia
            if now.month == 12:
                next_date = now.replace(year=now.year + 1, month=1, day=schedule.dia_mes)
            else:
                next_date = now.replace(month=now.month + 1, day=schedule.dia_mes)
        else:
            next_date = now + timedelta(days=1)
        
        return datetime.combine(next_date.date(), hora_envio)

