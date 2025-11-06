"""
Sistema de Alertas Automáticos
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from .models import Atestado, Upload
from datetime import datetime, timedelta
from typing import List, Dict, Any

class AlertasSystem:
    """Sistema de alertas automáticos"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def detectar_alertas(self, client_id: int = 1, mes_inicio: str = None, mes_fim: str = None) -> List[Dict[str, Any]]:
        """Detecta alertas baseados em regras configuráveis"""
        alertas = []
        
        # Busca métricas gerais
        query = self.db.query(
            func.sum(Atestado.dias_atestados).label('total_dias'),
            func.count(Atestado.id).label('total_registros')
        ).join(Upload).filter(Upload.client_id == client_id)
        
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        
        result = query.first()
        total_dias = float(result.total_dias or 0) if result else 0
        total_registros = int(result.total_registros or 0) if result else 0
        
        # Thresholds configuráveis (pode vir de Config depois)
        THRESHOLD_ALTO_ABSENTEISMO_FUNCIONARIO = 10  # dias
        THRESHOLD_ALTO_ABSENTEISMO_SETOR = 50  # dias
        THRESHOLD_FREQUENCIA_ATESTADOS = 5  # número de atestados
        
        # 1. Funcionários com alto absenteísmo
        query_func = self.db.query(
            Atestado.nomecompleto,
            Atestado.setor,
            func.sum(Atestado.dias_atestados).label('dias_perdidos'),
            func.count(Atestado.id).label('quantidade_atestados')
        ).join(Upload).filter(Upload.client_id == client_id)
        
        if mes_inicio:
            query_func = query_func.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query_func = query_func.filter(Upload.mes_referencia <= mes_fim)
        
        query_func = query_func.group_by(Atestado.nomecompleto, Atestado.setor).having(
            func.sum(Atestado.dias_atestados) >= THRESHOLD_ALTO_ABSENTEISMO_FUNCIONARIO
        ).order_by(func.sum(Atestado.dias_atestados).desc())
        
        funcionarios_alto = query_func.limit(10).all()
        
        for func_data in funcionarios_alto:
            alertas.append({
                'tipo': 'funcionario_alto_absenteismo',
                'severidade': 'alta',
                'titulo': 'Funcionário com Alto Absenteísmo',
                'mensagem': f"{func_data.nomecompleto} ({func_data.setor}) tem {int(func_data.dias_perdidos)} dias perdidos e {func_data.quantidade_atestados} atestados",
                'dados': {
                    'nome': func_data.nomecompleto,
                    'setor': func_data.setor,
                    'dias_perdidos': int(func_data.dias_perdidos),
                    'quantidade_atestados': func_data.quantidade_atestados
                }
            })
        
        # 2. Setores críticos
        query_setor = self.db.query(
            Atestado.setor,
            func.sum(Atestado.dias_atestados).label('dias_perdidos'),
            func.count(Atestado.id).label('quantidade_atestados')
        ).join(Upload).filter(
            Upload.client_id == client_id,
            Atestado.setor.isnot(None),
            Atestado.setor != ''
        )
        
        if mes_inicio:
            query_setor = query_setor.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query_setor = query_setor.filter(Upload.mes_referencia <= mes_fim)
        
        query_setor = query_setor.group_by(Atestado.setor).having(
            func.sum(Atestado.dias_atestados) >= THRESHOLD_ALTO_ABSENTEISMO_SETOR
        ).order_by(func.sum(Atestado.dias_atestados).desc())
        
        setores_criticos = query_setor.limit(5).all()
        
        for setor_data in setores_criticos:
            alertas.append({
                'tipo': 'setor_critico',
                'severidade': 'media',
                'titulo': 'Setor com Alto Absenteísmo',
                'mensagem': f"Setor {setor_data.setor} apresenta {int(setor_data.dias_perdidos)} dias perdidos",
                'dados': {
                    'setor': setor_data.setor,
                    'dias_perdidos': int(setor_data.dias_perdidos),
                    'quantidade_atestados': setor_data.quantidade_atestados
                }
            })
        
        # 3. Funcionários com muitos atestados frequentes
        query_freq = self.db.query(
            Atestado.nomecompleto,
            Atestado.setor,
            func.count(Atestado.id).label('quantidade_atestados')
        ).join(Upload).filter(Upload.client_id == client_id)
        
        if mes_inicio:
            query_freq = query_freq.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query_freq = query_freq.filter(Upload.mes_referencia <= mes_fim)
        
        query_freq = query_freq.group_by(Atestado.nomecompleto, Atestado.setor).having(
            func.count(Atestado.id) >= THRESHOLD_FREQUENCIA_ATESTADOS
        ).order_by(func.count(Atestado.id).desc())
        
        funcionarios_frequentes = query_freq.limit(10).all()
        
        for func_data in funcionarios_frequentes:
            # Só adiciona se não foi adicionado no alerta de alto absenteísmo
            if not any(a['tipo'] == 'funcionario_alto_absenteismo' and 
                      a['dados']['nome'] == func_data.nomecompleto for a in alertas):
                alertas.append({
                    'tipo': 'funcionario_frequente',
                    'severidade': 'media',
                    'titulo': 'Funcionário com Muitos Atestados',
                    'mensagem': f"{func_data.nomecompleto} ({func_data.setor}) tem {func_data.quantidade_atestados} atestados no período",
                    'dados': {
                        'nome': func_data.nomecompleto,
                        'setor': func_data.setor,
                        'quantidade_atestados': func_data.quantidade_atestados
                    }
                })
        
        # 4. CID frequente (doenças recorrentes)
        query_cid = self.db.query(
            Atestado.cid,
            Atestado.diagnostico,
            func.count(Atestado.id).label('quantidade')
        ).join(Upload).filter(
            Upload.client_id == client_id,
            Atestado.cid.isnot(None),
            Atestado.cid != ''
        )
        
        if mes_inicio:
            query_cid = query_cid.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query_cid = query_cid.filter(Upload.mes_referencia <= mes_fim)
        
        query_cid = query_cid.group_by(Atestado.cid, Atestado.diagnostico).having(
            func.count(Atestado.id) >= 10  # Threshold: 10+ ocorrências
        ).order_by(func.count(Atestado.id).desc())
        
        cid_frequente = query_cid.first()
        
        if cid_frequente:
            alertas.append({
                'tipo': 'cid_frequente',
                'severidade': 'baixa',
                'titulo': 'Doença Frequente',
                'mensagem': f"CID {cid_frequente.cid} ({cid_frequente.diagnostico or 'N/A'}) aparece {cid_frequente.quantidade} vezes",
                'dados': {
                    'cid': cid_frequente.cid,
                    'diagnostico': cid_frequente.diagnostico,
                    'quantidade': cid_frequente.quantidade
                }
            })
        
        return alertas

