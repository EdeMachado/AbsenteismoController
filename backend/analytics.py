"""
Analytics - Cálculos de métricas e análises
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from .models import Atestado, Upload, Client
from datetime import datetime, timedelta
from typing import Dict, List, Any
import calendar

class Analytics:
    """Classe para cálculos analíticos"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def metricas_gerais(self, client_id: int, mes_inicio: str = None, mes_fim: str = None) -> Dict[str, Any]:
        """Calcula métricas gerais"""
        query = self.db.query(Atestado).join(Upload).filter(Upload.client_id == client_id)
        
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        
        atestados = query.all()
        
        # Separar por tipo - Usa o código TIPOINFOATEST: 1=Dias, 3=Horas
        atestados_dias = [a for a in atestados if a.tipo_info_atestado == 1]
        atestados_horas = [a for a in atestados if a.tipo_info_atestado == 3]
        
        total_atestados = len(atestados)
        total_atestados_dias = len(atestados_dias)
        total_atestados_horas = len(atestados_horas)
        
        # Dias e Horas perdidos - APENAS dos atestados tipo DIAS (tipo_info_atestado = 1)
        total_dias_perdidos = sum(a.numero_dias_atestado for a in atestados_dias)
        total_horas_perdidas = sum(a.horas_perdidas for a in atestados_dias)
        
        # Taxa de absenteísmo (simplificada - pode ajustar conforme necessário)
        # Fórmula: (Horas perdidas / Horas disponíveis) * 100
        # Assumindo jornada de 8h/dia, 22 dias úteis/mês
        horas_disponiveis = 176 * len(set(a.nome_funcionario for a in atestados))  # 22 dias * 8h
        taxa_absenteismo = (total_horas_perdidas / horas_disponiveis * 100) if horas_disponiveis > 0 else 0
        
        return {
            'total_atestados': total_atestados,
            'total_atestados_dias': total_atestados_dias,
            'total_atestados_horas': total_atestados_horas,
            'total_dias_perdidos': round(total_dias_perdidos, 2),
            'total_horas_perdidas': round(total_horas_perdidas, 2),
            'taxa_absenteismo': round(taxa_absenteismo, 2),
            'funcionarios_afetados': len(set(a.nome_funcionario for a in atestados if a.nome_funcionario))
        }
    
    def top_cids(self, client_id: int, limit: int = 5, mes_inicio: str = None, mes_fim: str = None) -> List[Dict[str, Any]]:
        """TOP CIDs mais frequentes"""
        query = self.db.query(
            Atestado.cid,
            Atestado.descricao_cid,
            func.count(Atestado.id).label('quantidade'),
            func.sum(Atestado.dias_perdidos).label('dias_perdidos')
        ).join(Upload).filter(
            Upload.client_id == client_id,
            Atestado.cid != '',
            Atestado.cid.isnot(None)
        )
        
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        
        query = query.group_by(Atestado.cid, Atestado.descricao_cid).order_by(func.count(Atestado.id).desc()).limit(limit)
        
        results = query.all()
        
        return [
            {
                'cid': r.cid,
                'descricao': r.descricao_cid or 'Não informado',
                'quantidade': r.quantidade,
                'dias_perdidos': round(r.dias_perdidos or 0, 2)
            }
            for r in results
        ]
    
    def top_setores(self, client_id: int, limit: int = 5, mes_inicio: str = None, mes_fim: str = None) -> List[Dict[str, Any]]:
        """TOP setores com mais atestados"""
        query = self.db.query(
            Atestado.setor,
            func.count(Atestado.id).label('quantidade'),
            func.sum(Atestado.dias_perdidos).label('dias_perdidos'),
            func.sum(Atestado.horas_perdidas).label('horas_perdidas')
        ).join(Upload).filter(
            Upload.client_id == client_id,
            Atestado.setor != '',
            Atestado.setor.isnot(None)
        )
        
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        
        query = query.group_by(Atestado.setor).order_by(func.count(Atestado.id).desc()).limit(limit)
        
        results = query.all()
        
        return [
            {
                'setor': r.setor,
                'quantidade': r.quantidade,
                'dias_perdidos': round(r.dias_perdidos or 0, 2),
                'horas_perdidas': round(r.horas_perdidas or 0, 2)
            }
            for r in results
        ]
    
    def top_funcionarios(self, client_id: int, limit: int = 10, mes_inicio: str = None, mes_fim: str = None) -> List[Dict[str, Any]]:
        """TOP funcionários com mais atestados"""
        query = self.db.query(
            Atestado.nome_funcionario,
            Atestado.setor,
            Atestado.genero,
            func.count(Atestado.id).label('quantidade'),
            func.sum(Atestado.dias_perdidos).label('dias_perdidos'),
            func.sum(Atestado.horas_perdidas).label('horas_perdidas')
        ).join(Upload).filter(
            Upload.client_id == client_id,
            Atestado.nome_funcionario != '',
            Atestado.nome_funcionario.isnot(None)
        )
        
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        
        query = query.group_by(Atestado.nome_funcionario, Atestado.setor, Atestado.genero).order_by(func.count(Atestado.id).desc()).limit(limit)
        
        results = query.all()
        
        return [
            {
                'nome': r.nome_funcionario,
                'setor': r.setor or 'Não informado',
                'genero': r.genero or '-',
                'quantidade': r.quantidade,
                'dias_perdidos': round(r.dias_perdidos or 0, 2),
                'horas_perdidas': round(r.horas_perdidas or 0, 2)
            }
            for r in results
        ]
    
    def evolucao_mensal(self, client_id: int, meses: int = 12) -> List[Dict[str, Any]]:
        """Evolução mensal dos atestados"""
        query = self.db.query(
            Upload.mes_referencia,
            func.count(Atestado.id).label('quantidade'),
            func.sum(Atestado.dias_perdidos).label('dias_perdidos'),
            func.sum(Atestado.horas_perdidas).label('horas_perdidas')
        ).join(Upload).filter(
            Upload.client_id == client_id
        ).group_by(Upload.mes_referencia).order_by(Upload.mes_referencia.desc()).limit(meses)
        
        results = query.all()
        
        dados = [
            {
                'mes': r.mes_referencia,
                'quantidade': r.quantidade,
                'dias_perdidos': round(r.dias_perdidos or 0, 2),
                'horas_perdidas': round(r.horas_perdidas or 0, 2)
            }
            for r in results
        ]
        
        # Retorna em ordem cronológica
        return list(reversed(dados))
    
    def distribuicao_genero(self, client_id: int, mes_inicio: str = None, mes_fim: str = None) -> List[Dict[str, Any]]:
        """Distribuição por gênero"""
        query = self.db.query(
            Atestado.genero,
            func.count(Atestado.id).label('quantidade'),
            func.sum(Atestado.dias_perdidos).label('dias_perdidos')
        ).join(Upload).filter(
            Upload.client_id == client_id,
            Atestado.genero != '',
            Atestado.genero.isnot(None)
        )
        
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        
        query = query.group_by(Atestado.genero)
        
        results = query.all()
        
        return [
            {
                'genero': r.genero,
                'quantidade': r.quantidade,
                'dias_perdidos': round(r.dias_perdidos or 0, 2)
            }
            for r in results
        ]
    
    def comparativo_periodos(self, client_id: int, periodo1: tuple, periodo2: tuple) -> Dict[str, Any]:
        """Compara dois períodos"""
        metricas1 = self.metricas_gerais(client_id, periodo1[0], periodo1[1])
        metricas2 = self.metricas_gerais(client_id, periodo2[0], periodo2[1])
        
        def calcular_variacao(atual, anterior):
            if anterior == 0:
                return 100 if atual > 0 else 0
            return round(((atual - anterior) / anterior) * 100, 2)
        
        return {
            'periodo1': metricas1,
            'periodo2': metricas2,
            'variacoes': {
                'atestados': calcular_variacao(metricas2['total_atestados'], metricas1['total_atestados']),
                'dias': calcular_variacao(metricas2['total_dias_perdidos'], metricas1['total_dias_perdidos']),
                'horas': calcular_variacao(metricas2['total_horas_perdidas'], metricas1['total_horas_perdidas']),
                'taxa': calcular_variacao(metricas2['taxa_absenteismo'], metricas1['taxa_absenteismo'])
            }
        }
