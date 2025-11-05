"""
Analytics - Cálculos de métricas e análises
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, or_
from .models import Atestado, Upload, Client
from datetime import datetime, timedelta
from typing import Dict, List, Any, Union
import calendar

class Analytics:
    """Classe para cálculos analíticos"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def metricas_gerais(self, client_id: int, mes_inicio: str = None, mes_fim: str = None, funcionario = None, setor = None) -> Dict[str, Any]:
        """
        Calcula métricas gerais - CÓDIGO NOVO E LIMPO
        Soma diretamente do banco usando SQL SUM
        """
        from sqlalchemy import or_
        
        # Query básica - busca todos os atestados do cliente
        query = self.db.query(
            func.sum(Atestado.dias_atestados).label('total_dias'),
            func.sum(Atestado.horas_perdi).label('total_horas'),
            func.count(Atestado.id).label('total_registros')
        ).join(Upload).filter(Upload.client_id == client_id)
        
        # Aplica filtros de data se fornecidos
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        
        # Aplica filtros usando helper
        from .analytics_helper import aplicar_filtro_funcionario, aplicar_filtro_setor
        query = aplicar_filtro_funcionario(query, funcionario)
        query = aplicar_filtro_setor(query, setor)
        
        # Executa query
        result = query.first()
        
        # Extrai valores (None vira 0)
        total_dias = float(result.total_dias or 0) if result and result.total_dias else 0.0
        total_horas = float(result.total_horas or 0) if result and result.total_horas else 0.0
        total_registros = int(result.total_registros or 0) if result else 0
        
        # Conta funcionários únicos
        funcionarios_query = self.db.query(Atestado.nomecompleto).join(Upload).filter(
            Upload.client_id == client_id
        )
        if mes_inicio:
            funcionarios_query = funcionarios_query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            funcionarios_query = funcionarios_query.filter(Upload.mes_referencia <= mes_fim)
        # Aplica filtros usando helper
        from .analytics_helper import aplicar_filtro_funcionario, aplicar_filtro_setor
        funcionarios_query = aplicar_filtro_funcionario(funcionarios_query, funcionario)
        funcionarios_query = aplicar_filtro_setor(funcionarios_query, setor)
        
        funcionarios_unicos = len(set([f[0] for f in funcionarios_query.all() if f[0]]))
        
        # Retorna métricas
        return {
            'total_atestados_dias': round(total_dias, 2),
            'total_dias_perdidos': round(total_dias, 2),  # Mesmo valor
            'total_horas_perdidas': round(total_horas, 2),
            'total_atestados': total_registros,
            'funcionarios_afetados': funcionarios_unicos
        }
    
    def top_cids(self, client_id: int, limit: int = 5, mes_inicio: str = None, mes_fim: str = None, funcionario: str = None, setor: str = None) -> List[Dict[str, Any]]:
        """TOP CIDs mais frequentes"""
        cids_genericos = ['Z00.0', 'Z00.1', 'Z52.0', 'Z76.0', 'Z76.1']
        
        query = self.db.query(
            Atestado.cid,
            Atestado.diagnostico,
            func.count(Atestado.id).label('quantidade'),
            func.sum(Atestado.dias_atestados).label('dias_perdidos')
        ).join(Upload).filter(
            Upload.client_id == client_id,
            Atestado.cid != '',
            Atestado.cid.isnot(None),
            ~Atestado.cid.in_(cids_genericos)
        )
        
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        # Aplica filtros usando helper
        from .analytics_helper import aplicar_filtro_funcionario, aplicar_filtro_setor
        query = aplicar_filtro_funcionario(query, funcionario)
        query = aplicar_filtro_setor(query, setor)
        
        query = query.group_by(Atestado.cid, Atestado.diagnostico).order_by(func.count(Atestado.id).desc()).limit(limit)
        
        results = query.all()
        
        return [
            {
                'cid': r.cid,
                'descricao': r.diagnostico or 'Não informado',
                'quantidade': r.quantidade,
                'dias_perdidos': round(r.dias_perdidos or 0, 2)
            }
            for r in results
        ]
    
    def top_setores(self, client_id: int, limit: int = 5, mes_inicio: str = None, mes_fim: str = None, funcionario: str = None, setor: str = None) -> List[Dict[str, Any]]:
        """TOP Setores"""
        query = self.db.query(
            Atestado.setor,
            func.count(Atestado.id).label('quantidade'),
            func.sum(Atestado.dias_atestados).label('dias_perdidos'),
            func.sum(Atestado.horas_perdi).label('horas_perdidas')
        ).join(Upload).filter(
            Upload.client_id == client_id,
            Atestado.setor != '',
            Atestado.setor.isnot(None)
        )
        
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        
        # Aplica filtros usando helper
        from .analytics_helper import aplicar_filtro_funcionario, aplicar_filtro_setor
        query = aplicar_filtro_funcionario(query, funcionario)
        query = aplicar_filtro_setor(query, setor)

        
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
    
    def top_funcionarios(self, client_id: int, limit: int = 10, mes_inicio: str = None, mes_fim: str = None, funcionario: str = None, setor: str = None) -> List[Dict[str, Any]]:
        """TOP Funcionários - Agrupa apenas por nome para somar todos os dias"""
        query = self.db.query(
            Atestado.nomecompleto,
            func.count(Atestado.id).label('quantidade'),
            func.sum(Atestado.dias_atestados).label('dias_perdidos'),
            func.sum(Atestado.horas_perdi).label('horas_perdidas')
        ).join(Upload).filter(
            Upload.client_id == client_id
        ).filter(
            (Atestado.nomecompleto != '') | (Atestado.nome_funcionario != ''),
            (Atestado.nomecompleto.isnot(None)) | (Atestado.nome_funcionario.isnot(None))
        )
        
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        # Aplica filtros usando helper
        from .analytics_helper import aplicar_filtro_funcionario, aplicar_filtro_setor
        query = aplicar_filtro_funcionario(query, funcionario)
        query = aplicar_filtro_setor(query, setor)
        
        # Agrupa apenas por nome para somar todos os dias do funcionário
        query = query.group_by(Atestado.nomecompleto).order_by(func.sum(Atestado.dias_atestados).desc()).limit(limit)
        
        results = query.all()
        
        # Busca setor e gênero do primeiro registro de cada funcionário para exibição
        funcionarios_completos = []
        for r in results:
            # Busca setor e genero do primeiro registro desse funcionário
            primeiro = self.db.query(Atestado.setor, Atestado.genero).join(Upload).filter(
                Upload.client_id == client_id,
                Atestado.nomecompleto == r.nomecompleto
            ).first()
            
            funcionarios_completos.append({
                'nome': r.nomecompleto or 'Não informado',
                'setor': primeiro.setor if primeiro else 'Não informado',
                'genero': primeiro.genero if primeiro else '-',
                'quantidade': r.quantidade,
                'dias_perdidos': round(r.dias_perdidos or 0, 2),
                'horas_perdidas': round(r.horas_perdidas or 0, 2)
            })
        
        return funcionarios_completos
    
    def evolucao_mensal(self, client_id: int, meses: int = 12, mes_inicio: str = None, mes_fim: str = None, funcionario: str = None, setor: str = None) -> List[Dict[str, Any]]:
        """Evolução mensal dos atestados"""
        query = self.db.query(
            Upload.mes_referencia,
            func.count(Atestado.id).label('quantidade'),
            func.sum(Atestado.dias_atestados).label('dias_perdidos'),
            func.sum(Atestado.horas_perdi).label('horas_perdidas')
        ).join(Upload).filter(
            Upload.client_id == client_id
        )
        
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        # Aplica filtros usando helper
        from .analytics_helper import aplicar_filtro_funcionario, aplicar_filtro_setor
        query = aplicar_filtro_funcionario(query, funcionario)
        query = aplicar_filtro_setor(query, setor)
        
        query = query.group_by(Upload.mes_referencia).order_by(Upload.mes_referencia.desc()).limit(meses)
        
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
        
        return list(reversed(dados))
    
    def distribuicao_genero(self, client_id: int, mes_inicio: str = None, mes_fim: str = None, funcionario: str = None, setor: str = None) -> List[Dict[str, Any]]:
        """Distribuição por gênero"""
        query = self.db.query(
            Atestado.genero,
            func.count(Atestado.id).label('quantidade'),
            func.sum(Atestado.dias_atestados).label('dias_perdidos')
        ).join(Upload).filter(
            Upload.client_id == client_id,
            Atestado.genero != '',
            Atestado.genero.isnot(None)
        )
        
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        
        # Aplica filtros usando helper
        from .analytics_helper import aplicar_filtro_funcionario, aplicar_filtro_setor
        query = aplicar_filtro_funcionario(query, funcionario)
        query = aplicar_filtro_setor(query, setor)

        
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
    
    def top_escalas(self, client_id: int, limit: int = 10, mes_inicio: str = None, mes_fim: str = None, funcionario: str = None, setor: str = None) -> List[Dict[str, Any]]:
        """TOP Escalas com mais atestados"""
        query = self.db.query(
            Atestado.escala,
            func.count(Atestado.id).label('quantidade'),
            func.sum(Atestado.dias_atestados).label('dias_perdidos')
        ).join(Upload).filter(
            Upload.client_id == client_id,
            Atestado.escala != '',
            Atestado.escala.isnot(None)
        )
        
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        
        # Aplica filtros usando helper
        from .analytics_helper import aplicar_filtro_funcionario, aplicar_filtro_setor
        query = aplicar_filtro_funcionario(query, funcionario)
        query = aplicar_filtro_setor(query, setor)

        
        query = query.group_by(Atestado.escala).order_by(func.count(Atestado.id).desc()).limit(limit)
        
        results = query.all()
        
        return [
            {
                'escala': r.escala or 'Não informado',
                'quantidade': r.quantidade,
                'dias_perdidos': round(r.dias_perdidos or 0, 2)
            }
            for r in results
        ]
    
    def top_motivos(self, client_id: int, limit: int = 10, mes_inicio: str = None, mes_fim: str = None, funcionario: str = None, setor: str = None) -> List[Dict[str, Any]]:
        """TOP Motivos de Incidência com mais atestados (com percentual)"""
        # Primeiro calcula o total
        total_query = self.db.query(func.count(Atestado.id)).join(Upload).filter(
            Upload.client_id == client_id,
            Atestado.motivo_atestado != '',
            Atestado.motivo_atestado.isnot(None)
        )
        
        if mes_inicio:
            total_query = total_query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            total_query = total_query.filter(Upload.mes_referencia <= mes_fim)
        if funcionario:
            total_query = total_query.filter(
                (Atestado.nomecompleto == funcionario) | (Atestado.nome_funcionario == funcionario)
            )
        if setor:
            total_query = total_query.filter(Atestado.setor == setor)
        
        total = total_query.scalar() or 1
        
        # Agora busca os motivos
        query = self.db.query(
            Atestado.motivo_atestado,
            func.count(Atestado.id).label('quantidade')
        ).join(Upload).filter(
            Upload.client_id == client_id,
            Atestado.motivo_atestado != '',
            Atestado.motivo_atestado.isnot(None)
        )
        
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        
        # Aplica filtros usando helper
        from .analytics_helper import aplicar_filtro_funcionario, aplicar_filtro_setor
        query = aplicar_filtro_funcionario(query, funcionario)
        query = aplicar_filtro_setor(query, setor)

        
        query = query.group_by(Atestado.motivo_atestado).order_by(func.count(Atestado.id).desc()).limit(limit)
        
        results = query.all()
        
        return [
            {
                'motivo': r.motivo_atestado or 'Não informado',
                'quantidade': r.quantidade,
                'percentual': round((r.quantidade / total * 100), 2) if total > 0 else 0
            }
            for r in results
        ]
    
    def dias_perdidos_por_centro_custo(self, client_id: int, limit: int = 10, mes_inicio: str = None, mes_fim: str = None, funcionario: str = None, setor: str = None) -> List[Dict[str, Any]]:
        """TOP Setores por dias perdidos (usando setor como centro de custo)"""
        query = self.db.query(
            Atestado.setor,
            func.count(Atestado.id).label('quantidade'),
            func.sum(Atestado.dias_atestados).label('dias_perdidos'),
            func.sum(Atestado.horas_perdi).label('horas_perdidas')
        ).join(Upload).filter(
            Upload.client_id == client_id,
            Atestado.setor != '',
            Atestado.setor.isnot(None)
        )
        
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        
        # Aplica filtros usando helper
        from .analytics_helper import aplicar_filtro_funcionario, aplicar_filtro_setor
        query = aplicar_filtro_funcionario(query, funcionario)
        query = aplicar_filtro_setor(query, setor)

        
        query = query.group_by(Atestado.setor).order_by(func.sum(Atestado.dias_atestados).desc()).limit(limit)
        
        results = query.all()
        
        return [
            {
                'centro_custo': r.setor or 'Não informado',
                'quantidade': r.quantidade,
                'dias_perdidos': round(r.dias_perdidos or 0, 2),
                'horas_perdidas': round(r.horas_perdidas or 0, 2)
            }
            for r in results
        ]
    
    def distribuicao_dias_por_atestado(self, client_id: int, mes_inicio: str = None, mes_fim: str = None, funcionario: str = None, setor: str = None) -> List[Dict[str, Any]]:
        """Distribuição de dias por atestado (histograma)"""
        query = self.db.query(Atestado.dias_atestados).join(Upload).filter(
            Upload.client_id == client_id,
            Atestado.dias_atestados > 0
        )
        
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        # Aplica filtros usando helper
        from .analytics_helper import aplicar_filtro_funcionario, aplicar_filtro_setor
        query = aplicar_filtro_funcionario(query, funcionario)
        query = aplicar_filtro_setor(query, setor)
        
        dias_list = [float(d[0]) for d in query.all() if d[0] and d[0] > 0]
        
        # Cria faixas: 1 dia, 2 dias, 3-5 dias, 6-10 dias, 11-15 dias, 16-30 dias, 31+ dias
        faixas = {
            '1 dia': 0,
            '2 dias': 0,
            '3-5 dias': 0,
            '6-10 dias': 0,
            '11-15 dias': 0,
            '16-30 dias': 0,
            '31+ dias': 0
        }
        
        for dias in dias_list:
            if dias == 1:
                faixas['1 dia'] += 1
            elif dias == 2:
                faixas['2 dias'] += 1
            elif 3 <= dias <= 5:
                faixas['3-5 dias'] += 1
            elif 6 <= dias <= 10:
                faixas['6-10 dias'] += 1
            elif 11 <= dias <= 15:
                faixas['11-15 dias'] += 1
            elif 16 <= dias <= 30:
                faixas['16-30 dias'] += 1
            else:
                faixas['31+ dias'] += 1
        
        return [
            {'faixa': faixa, 'quantidade': quantidade}
            for faixa, quantidade in faixas.items()
            if quantidade > 0
        ]
    
    def media_dias_por_cid(self, client_id: int, limit: int = 10, mes_inicio: str = None, mes_fim: str = None, funcionario: str = None, setor: str = None) -> List[Dict[str, Any]]:
        """Média de dias por CID"""
        query = self.db.query(
            Atestado.cid,
            Atestado.diagnostico,
            func.count(Atestado.id).label('quantidade'),
            func.sum(Atestado.dias_atestados).label('total_dias'),
            func.avg(Atestado.dias_atestados).label('media_dias')
        ).join(Upload).filter(
            Upload.client_id == client_id,
            Atestado.cid != '',
            Atestado.cid.isnot(None),
            Atestado.dias_atestados > 0
        )
        
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        
        # Aplica filtros usando helper
        from .analytics_helper import aplicar_filtro_funcionario, aplicar_filtro_setor
        query = aplicar_filtro_funcionario(query, funcionario)
        query = aplicar_filtro_setor(query, setor)

        
        query = query.group_by(Atestado.cid, Atestado.diagnostico).order_by(func.avg(Atestado.dias_atestados).desc()).limit(limit)
        
        results = query.all()
        
        return [
            {
                'cid': r.cid,
                'diagnostico': r.diagnostico or 'Não informado',
                'quantidade': r.quantidade,
                'total_dias': round(r.total_dias or 0, 2),
                'media_dias': round(r.media_dias or 0, 2)
            }
            for r in results
        ]
    
    def dias_perdidos_por_motivo(self, client_id: int, limit: int = 10, mes_inicio: str = None, mes_fim: str = None, funcionario: str = None, setor: str = None) -> List[Dict[str, Any]]:
        """Dias perdidos por motivo de atestado"""
        query = self.db.query(
            Atestado.motivo_atestado,
            func.count(Atestado.id).label('quantidade'),
            func.sum(Atestado.dias_atestados).label('dias_perdidos')
        ).join(Upload).filter(
            Upload.client_id == client_id,
            Atestado.motivo_atestado != '',
            Atestado.motivo_atestado.isnot(None)
        )
        
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        
        # Aplica filtros usando helper
        from .analytics_helper import aplicar_filtro_funcionario, aplicar_filtro_setor
        query = aplicar_filtro_funcionario(query, funcionario)
        query = aplicar_filtro_setor(query, setor)

        
        query = query.group_by(Atestado.motivo_atestado).order_by(func.sum(Atestado.dias_atestados).desc()).limit(limit)
        
        results = query.all()
        
        return [
            {
                'motivo': r.motivo_atestado or 'Não informado',
                'quantidade': r.quantidade,
                'dias_perdidos': round(r.dias_perdidos or 0, 2)
            }
            for r in results
        ]
    
    def evolucao_por_setor(self, client_id: int, meses: int = 12, mes_inicio: str = None, mes_fim: str = None, funcionario: str = None, setor: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """Evolução de dias perdidos por setor ao longo dos meses"""
        # Busca todos os setores
        setores_query = self.db.query(Atestado.setor).join(Upload).filter(
            Upload.client_id == client_id,
            Atestado.setor != '',
            Atestado.setor.isnot(None)
        ).distinct()
        
        if mes_inicio:
            setores_query = setores_query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            setores_query = setores_query.filter(Upload.mes_referencia <= mes_fim)
        if funcionario:
            setores_query = setores_query.filter(
                (Atestado.nomecompleto == funcionario) | (Atestado.nome_funcionario == funcionario)
            )
        if setor:
            setores_query = setores_query.filter(Atestado.setor == setor)
        
        setores = [s[0] for s in setores_query.all() if s[0]]
        
        # Busca evolução mensal por setor
        query = self.db.query(
            Upload.mes_referencia,
            Atestado.setor,
            func.sum(Atestado.dias_atestados).label('dias_perdidos')
        ).join(Upload).filter(
            Upload.client_id == client_id,
            Atestado.setor != '',
            Atestado.setor.isnot(None)
        )
        
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        
        # Aplica filtros usando helper
        from .analytics_helper import aplicar_filtro_funcionario, aplicar_filtro_setor
        query = aplicar_filtro_funcionario(query, funcionario)
        query = aplicar_filtro_setor(query, setor)

        
        query = query.group_by(Upload.mes_referencia, Atestado.setor).order_by(Upload.mes_referencia)
        
        results = query.all()
        
        # Organiza por setor
        evolucao_por_setor = {setor: [] for setor in setores}
        meses_unicos = sorted(set([r.mes_referencia for r in results]))
        
        for mes in meses_unicos[-meses:]:  # Últimos N meses
            for setor in setores:
                dias = next((r.dias_perdidos for r in results if r.mes_referencia == mes and r.setor == setor), 0)
                evolucao_por_setor[setor].append({
                    'mes': mes,
                    'dias_perdidos': round(dias or 0, 2)
                })
        
        return evolucao_por_setor
    
    def comparativo_dias_horas(self, client_id: int, mes_inicio: str = None, mes_fim: str = None, funcionario: str = None, setor: str = None) -> List[Dict[str, Any]]:
        """Comparativo de dias vs horas perdidas por setor"""
        query = self.db.query(
            Atestado.setor,
            func.sum(Atestado.dias_atestados).label('dias_perdidos'),
            func.sum(Atestado.horas_perdi).label('horas_perdidas')
        ).join(Upload).filter(
            Upload.client_id == client_id,
            Atestado.setor != '',
            Atestado.setor.isnot(None)
        )
        
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        
        # Aplica filtros usando helper
        from .analytics_helper import aplicar_filtro_funcionario, aplicar_filtro_setor
        query = aplicar_filtro_funcionario(query, funcionario)
        query = aplicar_filtro_setor(query, setor)

        
        query = query.group_by(Atestado.setor).order_by(func.sum(Atestado.dias_atestados).desc())
        
        results = query.all()
        
        return [
            {
                'setor': r.setor or 'Não informado',
                'dias_perdidos': round(r.dias_perdidos or 0, 2),
                'horas_perdidas': round(r.horas_perdidas or 0, 2)
            }
            for r in results
        ]
    
    def frequencia_atestados_por_funcionario(self, client_id: int, mes_inicio: str = None, mes_fim: str = None, funcionario: str = None, setor: str = None) -> List[Dict[str, Any]]:
        """Frequência de atestados por funcionário (quantos têm 1, 2, 3+ atestados)"""
        query = self.db.query(
            Atestado.nomecompleto,
            func.count(Atestado.id).label('quantidade')
        ).join(Upload).filter(
            Upload.client_id == client_id,
            (Atestado.nomecompleto != '') | (Atestado.nome_funcionario != ''),
            (Atestado.nomecompleto.isnot(None)) | (Atestado.nome_funcionario.isnot(None))
        )
        
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        
        # Aplica filtros usando helper
        from .analytics_helper import aplicar_filtro_funcionario, aplicar_filtro_setor
        query = aplicar_filtro_funcionario(query, funcionario)
        query = aplicar_filtro_setor(query, setor)

        
        query = query.group_by(Atestado.nomecompleto)
        
        results = query.all()
        
        # Agrupa por frequência
        frequencias = {
            '1 atestado': 0,
            '2 atestados': 0,
            '3-5 atestados': 0,
            '6-10 atestados': 0,
            '11+ atestados': 0
        }
        
        for r in results:
            qtd = r.quantidade
            if qtd == 1:
                frequencias['1 atestado'] += 1
            elif qtd == 2:
                frequencias['2 atestados'] += 1
            elif 3 <= qtd <= 5:
                frequencias['3-5 atestados'] += 1
            elif 6 <= qtd <= 10:
                frequencias['6-10 atestados'] += 1
            else:
                frequencias['11+ atestados'] += 1
        
        return [
            {'frequencia': freq, 'quantidade': qtd}
            for freq, qtd in frequencias.items()
            if qtd > 0
        ]
    
    def dias_perdidos_setor_genero(self, client_id: int, mes_inicio: str = None, mes_fim: str = None, funcionario: str = None, setor: str = None) -> List[Dict[str, Any]]:
        """Dias perdidos por setor e gênero"""
        query = self.db.query(
            Atestado.setor,
            Atestado.genero,
            func.count(Atestado.id).label('quantidade'),
            func.sum(Atestado.dias_atestados).label('dias_perdidos')
        ).join(Upload).filter(
            Upload.client_id == client_id,
            Atestado.setor != '',
            Atestado.setor.isnot(None),
            Atestado.genero != '',
            Atestado.genero.isnot(None)
        )
        
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        
        # Aplica filtros usando helper
        from .analytics_helper import aplicar_filtro_funcionario, aplicar_filtro_setor
        query = aplicar_filtro_funcionario(query, funcionario)
        query = aplicar_filtro_setor(query, setor)

        
        query = query.group_by(Atestado.setor, Atestado.genero).order_by(Atestado.setor, Atestado.genero)
        
        results = query.all()
        
        return [
            {
                'setor': r.setor or 'Não informado',
                'genero': r.genero or '-',
                'genero_label': 'Masculino' if r.genero == 'M' else 'Feminino' if r.genero == 'F' else r.genero,
                'quantidade': r.quantidade,
                'dias_perdidos': round(r.dias_perdidos or 0, 2)
            }
            for r in results
        ]
