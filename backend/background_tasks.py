"""
Tarefas em background - agendador de relatórios e verificação de alertas
"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .database import SessionLocal
from .report_scheduler import ReportScheduler
from .alert_service import AlertService
from .models import Client

class BackgroundTaskManager:
    """Gerenciador de tarefas em background"""
    
    def __init__(self):
        self.running = False
        self.task = None
    
    async def start(self):
        """Inicia o gerenciador de tarefas"""
        self.running = True
        self.task = asyncio.create_task(self._run_tasks())
    
    async def stop(self):
        """Para o gerenciador de tarefas"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
    
    async def _run_tasks(self):
        """Loop principal de tarefas"""
        while self.running:
            try:
                # Processa relatórios agendados
                await self._process_reports()
                
                # Verifica alertas
                await self._check_alerts()
                
                # Aguarda 1 minuto antes da próxima verificação
                await asyncio.sleep(60)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Erro em tarefa background: {e}")
                await asyncio.sleep(60)
    
    async def _process_reports(self):
        """Processa relatórios agendados"""
        try:
            db = SessionLocal()
            try:
                scheduler = ReportScheduler(db)
                results = scheduler.process_scheduled_reports()
                if results:
                    print(f"📧 Processados {len(results)} relatórios agendados")
            finally:
                db.close()
        except Exception as e:
            print(f"Erro ao processar relatórios: {e}")
    
    async def _check_alerts(self):
        """Verifica regras de alerta"""
        try:
            db = SessionLocal()
            try:
                # Busca todas as empresas ativas
                clients = db.query(Client).all()
                alert_service = AlertService(db)
                
                for client in clients:
                    try:
                        alerts = alert_service.check_alert_rules(client.id)
                        if alerts:
                            print(f"⚠️ Criados {len(alerts)} alertas para empresa {client.id}")
                    except Exception as e:
                        print(f"Erro ao verificar alertas da empresa {client.id}: {e}")
            finally:
                db.close()
        except Exception as e:
            print(f"Erro ao verificar alertas: {e}")

# Instância global
background_manager = BackgroundTaskManager()

