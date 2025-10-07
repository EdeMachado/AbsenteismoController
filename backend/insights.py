"""
Insights - Geração automática de análises e recomendações
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
from .models import Atestado, Upload

class InsightsEngine:
    """Engine de geração de insights"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def gerar_insights(self, client_id: int) -> List[Dict[str, Any]]:
        """Gera insights automáticos"""
        insights = []
        
        # 1. TOP CID mais frequente
        top_cid = self.db.query(
            Atestado.cid,
            Atestado.descricao_cid,
            func.count(Atestado.id).label('qtd')
        ).join(Upload).filter(
            Upload.client_id == client_id,
            Atestado.cid != ''
        ).group_by(Atestado.cid, Atestado.descricao_cid).order_by(func.count(Atestado.id).desc()).first()
        
        if top_cid and top_cid.qtd > 0:
            insights.append({
                'tipo': 'alerta',
                'icone': '🩺',
                'titulo': f'CID {top_cid.cid} - Mais Frequente',
                'descricao': f'{top_cid.descricao_cid or "Doença não especificada"} aparece em {top_cid.qtd} atestados ({self._percentual(top_cid.qtd, client_id)}% do total)',
                'recomendacao': self._get_recomendacao_cid(top_cid.cid)
            })
        
        # 2. Setor com mais atestados
        top_setor = self.db.query(
            Atestado.setor,
            func.count(Atestado.id).label('qtd')
        ).join(Upload).filter(
            Upload.client_id == client_id,
            Atestado.setor != ''
        ).group_by(Atestado.setor).order_by(func.count(Atestado.id).desc()).first()
        
        if top_setor and top_setor.qtd > 0:
            insights.append({
                'tipo': 'atencao',
                'icone': '🏢',
                'titulo': f'Setor {top_setor.setor} - Maior Índice',
                'descricao': f'{top_setor.qtd} atestados registrados ({self._percentual(top_setor.qtd, client_id)}% do total)',
                'recomendacao': 'Avaliar condições de trabalho e ergonomia neste setor'
            })
        
        # 3. Análise de gênero
        generos = self.db.query(
            Atestado.genero,
            func.count(Atestado.id).label('qtd')
        ).join(Upload).filter(
            Upload.client_id == client_id,
            Atestado.genero != ''
        ).group_by(Atestado.genero).all()
        
        if len(generos) >= 2:
            total = sum(g.qtd for g in generos)
            for g in generos:
                pct = (g.qtd / total * 100) if total > 0 else 0
                if pct > 60:
                    insights.append({
                        'tipo': 'info',
                        'icone': '👥',
                        'titulo': f'Gênero {"Masculino" if g.genero == "M" else "Feminino"} - Maior Incidência',
                        'descricao': f'{pct:.1f}% dos atestados são de funcionários do sexo {"masculino" if g.genero == "M" else "feminino"}',
                        'recomendacao': 'Investigar possíveis causas específicas deste grupo'
                    })
        
        # 4. Tendência mensal
        ultimos_meses = self.db.query(
            Upload.mes_referencia,
            func.count(Atestado.id).label('qtd')
        ).join(Atestado).filter(
            Upload.client_id == client_id
        ).group_by(Upload.mes_referencia).order_by(Upload.mes_referencia.desc()).limit(2).all()
        
        if len(ultimos_meses) >= 2:
            atual = ultimos_meses[0].qtd
            anterior = ultimos_meses[1].qtd
            variacao = ((atual - anterior) / anterior * 100) if anterior > 0 else 0
            
            if abs(variacao) > 15:
                insights.append({
                    'tipo': 'tendencia' if variacao > 0 else 'positivo',
                    'icone': '📈' if variacao > 0 else '📉',
                    'titulo': f'Tendência: {"Aumento" if variacao > 0 else "Redução"} de {abs(variacao):.1f}%',
                    'descricao': f'Comparando {ultimos_meses[0].mes_referencia} ({atual} atestados) com {ultimos_meses[1].mes_referencia} ({anterior} atestados)',
                    'recomendacao': 'Monitorar nos próximos meses' if variacao > 0 else 'Manter as ações atuais'
                })
        
        # 5. Dias perdidos alto
        total_dias = self.db.query(
            func.sum(Atestado.dias_perdidos)
        ).join(Upload).filter(
            Upload.client_id == client_id,
            Atestado.tipo_info_atestado == 1
        ).scalar() or 0
        
        if total_dias > 500:
            insights.append({
                'tipo': 'alerta',
                'icone': '⚠️',
                'titulo': f'{int(total_dias)} Dias Perdidos',
                'descricao': 'Volume alto de dias perdidos pode impactar produtividade',
                'recomendacao': 'Implementar programa de saúde preventiva e qualidade de vida'
            })
        
        return insights
    
    def _percentual(self, valor: int, client_id: int) -> float:
        """Calcula percentual em relação ao total"""
        total = self.db.query(func.count(Atestado.id)).join(Upload).filter(
            Upload.client_id == client_id
        ).scalar() or 1
        
        return round((valor / total * 100), 1)
    
    def _get_recomendacao_cid(self, cid: str) -> str:
        """Retorna recomendação baseada no CID"""
        recomendacoes = {
            'M54': 'Implementar programa de ergonomia e ginástica laboral',
            'J00': 'Reforçar higiene e ventilação dos ambientes',
            'A09': 'Avaliar condições sanitárias e alimentação',
            'R51': 'Avaliar estresse e saúde mental dos colaboradores',
            'K29': 'Orientar sobre alimentação saudável',
            'F32': 'Implementar programa de saúde mental',
            'M79': 'Avaliar ergonomia e pausas durante o trabalho',
        }
        
        # Pega primeiros 3 caracteres do CID
        cid_grupo = cid[:3] if cid else ''
        
        return recomendacoes.get(cid_grupo, 'Investigar causas e implementar ações preventivas')


