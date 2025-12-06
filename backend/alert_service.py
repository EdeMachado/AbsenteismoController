"""
Serviço de alertas e notificações
"""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from .models import Alert, AlertRule, Client
from .analytics import Analytics
from .email_service import EmailService
import json

class AlertService:
    """Serviço para gerenciamento de alertas"""
    
    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailService()
    
    def create_alert(
        self,
        client_id: int,
        tipo: str,
        titulo: str,
        mensagem: str,
        severidade: str = "medium",
        dados: Optional[Dict[str, Any]] = None,
        enviar_email: bool = True
    ) -> Alert:
        """
        Cria um novo alerta
        
        Args:
            client_id: ID da empresa
            tipo: Tipo de alerta (limite_excedido, tendencia_alta, etc.)
            titulo: Título do alerta
            mensagem: Mensagem do alerta
            severidade: Severidade (low, medium, high, critical)
            dados: Dados adicionais do alerta
            enviar_email: Se deve enviar email automaticamente
        
        Returns:
            Alert criado
        """
        alert = Alert(
            client_id=client_id,
            tipo=tipo,
            titulo=titulo,
            mensagem=mensagem,
            severidade=severidade,
            dados=json.dumps(dados, ensure_ascii=False) if dados else None,
            created_at=datetime.now()
        )
        self.db.add(alert)
        self.db.flush()
        
        # Envia email se configurado
        if enviar_email and self.email_service.is_configured():
            client = self.db.query(Client).filter(Client.id == client_id).first()
            if client:
                # Busca emails das regras de alerta ou usa email da empresa
                emails = self._get_alert_emails(client_id)
                if emails:
                    self.email_service.send_alert_email(
                        emails,
                        client.nome_fantasia or client.nome,
                        titulo,
                        mensagem,
                        severidade
                    )
                    alert.enviado_email = True
        
        self.db.commit()
        self.db.refresh(alert)
        return alert
    
    def _get_alert_emails(self, client_id: int) -> List[str]:
        """Busca emails configurados para alertas da empresa"""
        emails = []
        
        # Busca emails das regras de alerta ativas
        rules = self.db.query(AlertRule).filter(
            AlertRule.client_id == client_id,
            AlertRule.is_active == True,
            AlertRule.enviar_email == True
        ).all()
        
        for rule in rules:
            if rule.emails_destinatarios:
                try:
                    rule_emails = json.loads(rule.emails_destinatarios)
                    if isinstance(rule_emails, list):
                        emails.extend(rule_emails)
                except:
                    pass
        
        # Remove duplicatas
        emails = list(set(emails))
        
        # Se não houver emails nas regras, usa email da empresa
        if not emails:
            client = self.db.query(Client).filter(Client.id == client_id).first()
            if client and client.email:
                emails.append(client.email)
        
        return emails
    
    def check_alert_rules(self, client_id: int) -> List[Alert]:
        """
        Verifica todas as regras de alerta e cria alertas se necessário
        
        Returns:
            Lista de alertas criados
        """
        rules = self.db.query(AlertRule).filter(
            AlertRule.client_id == client_id,
            AlertRule.is_active == True
        ).all()
        
        alerts_created = []
        analytics = Analytics(self.db)
        
        for rule in rules:
            alert = self._check_rule(rule, analytics, client_id)
            if alert:
                alerts_created.append(alert)
        
        return alerts_created
    
    def _check_rule(self, rule: AlertRule, analytics: Analytics, client_id: int) -> Optional[Alert]:
        """Verifica uma regra específica"""
        try:
            # Calcula período baseado na configuração
            hoje = datetime.now()
            if rule.periodo == "mensal":
                mes_inicio = (hoje - timedelta(days=30)).strftime("%Y-%m")
                mes_fim = hoje.strftime("%Y-%m")
            elif rule.periodo == "trimestral":
                mes_inicio = (hoje - timedelta(days=90)).strftime("%Y-%m")
                mes_fim = hoje.strftime("%Y-%m")
            elif rule.periodo == "anual":
                mes_inicio = (hoje - timedelta(days=365)).strftime("%Y-%m")
                mes_fim = hoje.strftime("%Y-%m")
            else:
                mes_inicio = None
                mes_fim = None
            
            # Busca métricas baseado no tipo de regra
            if rule.tipo == "dias_perdidos":
                metricas = analytics.metricas_gerais(client_id, mes_inicio, mes_fim)
                valor_atual = metricas.get('total_dias_perdidos', 0)
            elif rule.tipo == "taxa_absenteismo":
                metricas = analytics.metricas_gerais(client_id, mes_inicio, mes_fim)
                # Calcula taxa (dias perdidos / dias úteis estimados)
                dias_uteis = 22 if rule.periodo == "mensal" else 66 if rule.periodo == "trimestral" else 220
                valor_atual = (metricas.get('total_dias_perdidos', 0) / dias_uteis) * 100 if dias_uteis > 0 else 0
            else:
                return None
            
            # Verifica condição
            should_alert = False
            if rule.condicao == "maior_que" and valor_atual > rule.valor_limite:
                should_alert = True
            elif rule.condicao == "menor_que" and valor_atual < rule.valor_limite:
                should_alert = True
            elif rule.condicao == "igual" and valor_atual == rule.valor_limite:
                should_alert = True
            elif rule.condicao == "diferente" and valor_atual != rule.valor_limite:
                should_alert = True
            
            if should_alert:
                # Verifica se já existe alerta recente para evitar spam
                recent_alert = self.db.query(Alert).filter(
                    Alert.client_id == client_id,
                    Alert.tipo == rule.tipo,
                    Alert.is_resolvido == False,
                    Alert.created_at >= datetime.now() - timedelta(days=1)
                ).first()
                
                if not recent_alert:
                    titulo = f"Alerta: {rule.nome}"
                    mensagem = f"O valor atual ({valor_atual:.2f}) {rule.condicao.replace('_', ' ')} o limite configurado ({rule.valor_limite})."
                    
                    severidade = "high" if valor_atual > rule.valor_limite * 1.5 else "medium"
                    
                    return self.create_alert(
                        client_id=client_id,
                        tipo=rule.tipo,
                        titulo=titulo,
                        mensagem=mensagem,
                        severidade=severidade,
                        dados={"regra_id": rule.id, "valor_atual": valor_atual, "valor_limite": rule.valor_limite},
                        enviar_email=rule.enviar_email
                    )
        
        except Exception as e:
            print(f"Erro ao verificar regra {rule.id}: {e}")
        
        return None
    
    def get_alerts(
        self,
        client_id: Optional[int] = None,
        is_lido: Optional[bool] = None,
        is_resolvido: Optional[bool] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Busca alertas com filtros"""
        query = self.db.query(Alert)
        
        if client_id:
            query = query.filter(Alert.client_id == client_id)
        if is_lido is not None:
            query = query.filter(Alert.is_lido == is_lido)
        if is_resolvido is not None:
            query = query.filter(Alert.is_resolvido == is_resolvido)
        
        alerts = query.order_by(Alert.created_at.desc()).limit(limit).all()
        
        result = []
        for alert in alerts:
            alert_dict = {
                "id": alert.id,
                "client_id": alert.client_id,
                "client_name": alert.client.nome_fantasia or alert.client.nome if alert.client else None,
                "tipo": alert.tipo,
                "severidade": alert.severidade,
                "titulo": alert.titulo,
                "mensagem": alert.mensagem,
                "dados": json.loads(alert.dados) if alert.dados else None,
                "is_lido": alert.is_lido,
                "is_resolvido": alert.is_resolvido,
                "enviado_email": alert.enviado_email,
                "created_at": alert.created_at.isoformat() if alert.created_at else None,
                "lido_em": alert.lido_em.isoformat() if alert.lido_em else None,
                "resolvido_em": alert.resolvido_em.isoformat() if alert.resolvido_em else None
            }
            result.append(alert_dict)
        
        return result
    
    def mark_as_read(self, alert_id: int) -> bool:
        """Marca alerta como lido"""
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
        if alert:
            alert.is_lido = True
            alert.lido_em = datetime.now()
            self.db.commit()
            return True
        return False
    
    def mark_as_resolved(self, alert_id: int) -> bool:
        """Marca alerta como resolvido"""
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
        if alert:
            alert.is_resolvido = True
            alert.resolvido_em = datetime.now()
            self.db.commit()
            return True
        return False

