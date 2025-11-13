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
        # Usa float() para garantir precisão, evita arredondar antes de retornar
        total_dias = float(result.total_dias or 0) if result and result.total_dias is not None else 0.0
        total_horas = float(result.total_horas or 0) if result and result.total_horas is not None else 0.0
        total_registros = int(result.total_registros or 0) if result and result.total_registros is not None else 0
        
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
        # Para horas e dias, arredonda apenas para 2 decimais, mas preserva o valor exato para cálculos
        # IMPORTANTE: Não usa round() que pode causar diferenças - deixa o frontend arredondar
        return {
            'total_atestados_dias': total_dias,  # Soma dos dias (pode ter decimais)
            'total_dias_perdidos': total_dias,  # Mesmo valor
            'total_horas_perdidas': total_horas,  # Soma das horas (pode ter decimais)
            'total_atestados': total_registros,  # Número de registros (linhas da planilha)
            'total_registros': total_registros,  # Alias para compatibilidade
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
        # Ordena por dias perdidos (decrescente) para mostrar os TOP funcionários
        query = query.group_by(Atestado.nomecompleto).order_by(func.sum(Atestado.dias_atestados).desc()).limit(limit)
        
        results = query.all()
        
        # Busca setor e gênero do primeiro registro de cada funcionário para exibição
        funcionarios_completos = []
        for r in results:
            if not r.nomecompleto:
                continue  # Pula se não tiver nome
                
            # Busca setor e genero do primeiro registro desse funcionário
            primeiro = self.db.query(Atestado.setor, Atestado.genero).join(Upload).filter(
                Upload.client_id == client_id,
                Atestado.nomecompleto == r.nomecompleto
            ).first()
            
            funcionarios_completos.append({
                'nome': r.nomecompleto or 'Não informado',
                'setor': primeiro.setor if primeiro and primeiro.setor else 'Não informado',
                'genero': primeiro.genero if primeiro and primeiro.genero else '-',
                'quantidade': r.quantidade or 0,
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
        """TOP Centros de Custo por dias perdidos (centro_custo = setor)"""
        query = self.db.query(
            Atestado.setor,
            func.count(Atestado.id).label('quantidade'),
            func.sum(Atestado.dias_atestados).label('dias_perdidos'),
            func.sum(Atestado.horas_perdi).label('horas_perdidas')
        ).join(Upload).filter(
            Upload.client_id == client_id
        )
        
        # Filtra apenas registros com setor preenchido (centro de custo = setor)
        query = query.filter(
            or_(
                Atestado.setor != '',
                Atestado.setor.isnot(None)
            )
        )
        
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        
        # Aplica filtros usando helper
        from .analytics_helper import aplicar_filtro_funcionario, aplicar_filtro_setor
        query = aplicar_filtro_funcionario(query, funcionario)
        # Não aplica filtro de setor aqui, pois queremos ver todos os setores (centros de custo)
        
        query = query.group_by(Atestado.setor).order_by(func.sum(Atestado.dias_atestados).desc()).limit(limit)
        
        results = query.all()
        
        print(f"🔍 DEBUG dias_perdidos_por_centro_custo - client_id={client_id}, resultados encontrados: {len(results)}")
        
        resultado = []
        for r in results:
            dias = r.dias_perdidos if r.dias_perdidos is not None else 0
            if dias > 0:  # Só inclui se tiver dias > 0
                resultado.append({
                    'centro_custo': r.setor or 'Não informado',
                    'quantidade': r.quantidade or 0,
                    'dias_perdidos': round(dias, 2),
                    'horas_perdidas': round(r.horas_perdidas or 0, 2)
                })
                print(f"  - Centro Custo (Setor): {r.setor}, Dias: {round(dias, 2)}")
        
        print(f"📊 Total de centros de custo retornados: {len(resultado)}")
        return resultado
    
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
    
    def classificacao_funcionarios_roda_ouro(self, client_id: int, limit: int = 15, mes_inicio: str = None, mes_fim: str = None, funcionario: str = None, setor: str = None) -> List[Dict[str, Any]]:
        """Classificação por Funcionário - Roda de Ouro (conta atestados, não dias)"""
        query = self.db.query(
            Atestado.nomecompleto,
            func.count(Atestado.id).label('quantidade')
        ).join(Upload).filter(
            Upload.client_id == client_id,
            or_(
                Atestado.nomecompleto != '',
                Atestado.nomecompleto.isnot(None)
            )
        )
        
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        
        from .analytics_helper import aplicar_filtro_funcionario, aplicar_filtro_setor
        query = aplicar_filtro_funcionario(query, funcionario)
        query = aplicar_filtro_setor(query, setor)
        
        query = query.group_by(Atestado.nomecompleto).order_by(func.count(Atestado.id).desc()).limit(limit)
        
        results = query.all()
        
        return [
            {
                'nome': r.nomecompleto or 'Não informado',
                'quantidade': r.quantidade or 0
            }
            for r in results
        ]
    
    def classificacao_setores_roda_ouro(self, client_id: int, limit: int = 15, mes_inicio: str = None, mes_fim: str = None, funcionario: str = None, setor: str = None) -> List[Dict[str, Any]]:
        """Classificação por Setor - Roda de Ouro (soma dias de afastamento, não conta atestados)"""
        # Query mais flexível - aceita setor vazio ou NULL, mas agrupa por setor
        query = self.db.query(
            Atestado.setor,
            func.sum(Atestado.dias_atestados).label('dias_afastamento')
        ).join(Upload).filter(
            Upload.client_id == client_id
        )
        
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        
        from .analytics_helper import aplicar_filtro_funcionario, aplicar_filtro_setor
        query = aplicar_filtro_funcionario(query, funcionario)
        query = aplicar_filtro_setor(query, setor)
        
        # Agrupa por setor, incluindo NULLs como "Não informado"
        query = query.group_by(Atestado.setor).order_by(func.sum(Atestado.dias_atestados).desc()).limit(limit)
        
        results = query.all()
        
        print(f"🔍 DEBUG classificacao_setores_roda_ouro - client_id={client_id}, resultados encontrados: {len(results)}")
        
        resultado = []
        for r in results:
            dias = r.dias_afastamento if r.dias_afastamento is not None else 0
            setor_nome = r.setor if r.setor and r.setor.strip() else 'Não informado'
            if dias > 0:  # Só inclui setores com dias > 0
                resultado.append({
                    'setor': setor_nome,
                    'dias_afastamento': round(dias, 2)
                })
                print(f"  - Setor: {setor_nome}, Dias: {round(dias, 2)}")
        
        print(f"📊 Total de setores retornados: {len(resultado)}")
        return resultado
    
    def classificacao_doencas_roda_ouro(self, client_id: int, limit: int = 15, mes_inicio: str = None, mes_fim: str = None, funcionario: str = None, setor: str = None) -> List[Dict[str, Any]]:
        """Classificação por Doença - Roda de Ouro (agrupa por tipo de doença baseado no diagnóstico)"""
        # Busca todos os registros com diagnóstico
        query = self.db.query(
            Atestado.diagnostico,
            Atestado.cid,
            Atestado.descricao_cid,
            func.count(Atestado.id).label('quantidade')
        ).join(Upload).filter(
            Upload.client_id == client_id,
            or_(
                Atestado.diagnostico != '',
                Atestado.descricao_cid != ''
            ),
            or_(
                Atestado.diagnostico.isnot(None),
                Atestado.descricao_cid.isnot(None)
            )
        )
        
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        
        from .analytics_helper import aplicar_filtro_funcionario, aplicar_filtro_setor
        query = aplicar_filtro_funcionario(query, funcionario)
        query = aplicar_filtro_setor(query, setor)
        
        query = query.group_by(Atestado.diagnostico, Atestado.cid, Atestado.descricao_cid).order_by(func.count(Atestado.id).desc()).limit(limit * 2)
        
        results = query.all()
        
        # Agrupa por tipo de doença (categoriza diagnósticos)
        tipos_doenca = {}
        for r in results:
            diagnostico = (r.diagnostico or r.descricao_cid or '').upper()
            tipo = self._categorizar_doenca(diagnostico)
            
            if tipo not in tipos_doenca:
                tipos_doenca[tipo] = 0
            tipos_doenca[tipo] += r.quantidade or 0
        
        # Ordena e limita
        tipos_ordenados = sorted(tipos_doenca.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        return [
            {
                'tipo_doenca': tipo,
                'quantidade': quantidade
            }
            for tipo, quantidade in tipos_ordenados
        ]
    
    def _categorizar_doenca(self, diagnostico: str) -> str:
        """Categoriza diagnóstico em tipo de doença"""
        diagnostico_upper = diagnostico.upper()
        
        # Mapeamento de categorias
        if any(palavra in diagnostico_upper for palavra in ['OSTEOMUSCULAR', 'MUSCULO', 'OSSEO', 'ARTICULAÇÃO', 'ARTICULACAO', 'COLUNA', 'LOMBAR', 'CERVICAL', 'DORSAL']):
            if any(palavra in diagnostico_upper for palavra in ['TRAUMA', 'LESÃO', 'LESAO', 'FRATURA', 'ENTORSE', 'LUXAÇÃO', 'LUXACAO']):
                return 'OSTEOMUSCULAR - TRAUMA'
            else:
                return 'OSTEOMUSCULAR - CRÔNICO'
        elif any(palavra in diagnostico_upper for palavra in ['RESPIRATÓRIO', 'RESPIRATORIO', 'BRONQUITE', 'ASMA', 'PNEUMONIA', 'RINITE', 'SINUSITE']):
            return 'TRATO RESPIRATÓRIO'
        elif any(palavra in diagnostico_upper for palavra in ['GASTROINTESTINAL', 'GASTRICO', 'GASTRITE', 'ÚLCERA', 'ULCERA', 'INTESTINO', 'DIGESTIVO']):
            return 'TRATO GASTROINTESTINAL'
        elif any(palavra in diagnostico_upper for palavra in ['DERMATOLÓGICA', 'DERMATOLOGICA', 'PELE', 'DERMATITE', 'PSORÍASE', 'PSORIASE']):
            return 'DERMATOLÓGICAS'
        elif any(palavra in diagnostico_upper for palavra in ['OFTALMOLÓGICA', 'OFTALMOLOGICA', 'OLHO', 'VISÃO', 'VISAO', 'CONJUNTIVITE']):
            return 'OFTALMOLÓGICAS'
        elif any(palavra in diagnostico_upper for palavra in ['CARDIOLÓGICA', 'CARDIOLOGICA', 'CORAÇÃO', 'CORACAO', 'CARDIACO', 'HIPERTENSÃO', 'HIPERTENSAO']):
            return 'CARDIOLÓGICAS'
        elif any(palavra in diagnostico_upper for palavra in ['INFECCIOSA', 'INFECÇÃO', 'INFECCAO', 'VIRAL', 'BACTERIANA']):
            return 'DOENÇAS INFECCIOSAS'
        elif any(palavra in diagnostico_upper for palavra in ['ODONTOLÓGICA', 'ODONTOLOGICA', 'DENTAL', 'DENTE', 'GENGIVA']):
            return 'ODONTOLÓGICAS'
        elif any(palavra in diagnostico_upper for palavra in ['VASCULAR', 'VARIZES', 'CIRCULAÇÃO', 'CIRCULACAO']):
            return 'VASCULAR'
        else:
            return 'OUTRAS'
    
    def dias_atestados_por_ano_coerencia(self, client_id: int, mes_inicio: str = None, mes_fim: str = None, funcionario: str = None, setor: str = None) -> Dict[str, Any]:
        """Dias atestados por ano com coerência (COERENTE vs SEM COERÊNCIA)"""
        import json
        
        # Busca todos os registros
        query = self.db.query(
            Atestado.dias_atestados,
            Atestado.data_afastamento,
            Atestado.dados_originais,
            Upload.mes_referencia
        ).join(Upload).filter(
            Upload.client_id == client_id
        )
        
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        
        from .analytics_helper import aplicar_filtro_funcionario, aplicar_filtro_setor
        query = aplicar_filtro_funcionario(query, funcionario)
        query = aplicar_filtro_setor(query, setor)
        
        registros = query.all()
        
        # Agrupa por ano
        dados_por_ano = {}
        
        for r in registros:
            # Tenta obter ano da data de afastamento ou do mês de referência
            ano = None
            if r.data_afastamento:
                ano = str(r.data_afastamento.year)
            elif r.mes_referencia:
                ano = r.mes_referencia.split('-')[0]
            
            if not ano:
                continue
            
            if ano not in dados_por_ano:
                dados_por_ano[ano] = {'coerente': 0, 'sem_coerencia': 0}
            
            # Verifica coerência nos dados originais
            coerente = self._verificar_coerencia(r.dados_originais, r.dias_atestados)
            
            if coerente:
                dados_por_ano[ano]['coerente'] += r.dias_atestados or 0
            else:
                dados_por_ano[ano]['sem_coerencia'] += r.dias_atestados or 0
        
        # Converte para lista ordenada
        anos_ordenados = sorted(dados_por_ano.keys())
        
        return {
            'anos': anos_ordenados,
            'coerente': [dados_por_ano[ano]['coerente'] for ano in anos_ordenados],
            'sem_coerencia': [dados_por_ano[ano]['sem_coerencia'] for ano in anos_ordenados]
        }
    
    def _verificar_coerencia(self, dados_originais_json: str, dias_atestados: float) -> bool:
        """Verifica se o atestado é coerente baseado nos dados originais"""
        import json
        
        if not dados_originais_json:
            # Se não tem dados originais, assume coerente
            return True
        
        try:
            dados_originais = json.loads(dados_originais_json)
            
            # Procura campos relacionados a coerência
            for key, value in dados_originais.items():
                key_upper = str(key).upper()
                value_str = str(value).upper() if value else ''
                
                # Verifica se tem campo de coerência
                if 'COERENTE' in key_upper or 'COERENCIA' in key_upper:
                    if 'SIM' in value_str or 'S' in value_str or 'TRUE' in value_str or '1' in value_str:
                        return True
                    elif 'NÃO' in value_str or 'NAO' in value_str or 'N' in value_str or 'FALSE' in value_str or '0' in value_str:
                        return False
                
                # Verifica se tem campo "SEM COERÊNCIA"
                if 'SEM COER' in key_upper or 'SEM_COER' in key_upper:
                    if 'SIM' in value_str or 'S' in value_str or 'TRUE' in value_str or '1' in value_str:
                        return False
            
            # Se não encontrou campo de coerência, assume coerente por padrão
            return True
        except:
            # Se der erro ao parsear, assume coerente
            return True
    
    def analise_atestados_coerencia(self, client_id: int, mes_inicio: str = None, mes_fim: str = None, funcionario: str = None, setor: str = None) -> Dict[str, Any]:
        """Análise de atestados por coerência (para gráfico de rosca)"""
        import json
        
        query = self.db.query(
            Atestado.dias_atestados,
            Atestado.dados_originais,
            Upload.mes_referencia
        ).join(Upload).filter(
            Upload.client_id == client_id
        )
        
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        
        from .analytics_helper import aplicar_filtro_funcionario, aplicar_filtro_setor
        query = aplicar_filtro_funcionario(query, funcionario)
        query = aplicar_filtro_setor(query, setor)
        
        registros = query.all()
        
        total_coerente = 0
        total_sem_coerencia = 0
        
        for r in registros:
            dias = r.dias_atestados or 0
            coerente = self._verificar_coerencia(r.dados_originais, dias)
            
            if coerente:
                total_coerente += dias
            else:
                total_sem_coerencia += dias
        
        total = total_coerente + total_sem_coerencia
        
        return {
            'coerente': total_coerente,
            'sem_coerencia': total_sem_coerencia,
            'total': total,
            'percentual_coerente': (total_coerente / total * 100) if total > 0 else 0,
            'percentual_sem_coerencia': (total_sem_coerencia / total * 100) if total > 0 else 0
        }
    
    def tempo_servico_atestados(self, client_id: int, mes_inicio: str = None, mes_fim: str = None, funcionario: str = None, setor: str = None) -> List[Dict[str, Any]]:
        """Tempo de Serviço x Atestados - agrupa por ano (baseado em data_afastamento ou mes_referencia)"""
        query = self.db.query(
            Atestado.data_afastamento,
            Upload.mes_referencia,
            func.count(Atestado.id).label('quantidade')
        ).join(Upload).filter(
            Upload.client_id == client_id
        )
        
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        
        from .analytics_helper import aplicar_filtro_funcionario, aplicar_filtro_setor
        query = aplicar_filtro_funcionario(query, funcionario)
        query = aplicar_filtro_setor(query, setor)
        
        registros = query.all()
        
        # Agrupa por ano
        dados_por_ano = {}
        
        for r in registros:
            # Tenta obter ano da data de afastamento ou do mês de referência
            ano = None
            if r.data_afastamento:
                ano = str(r.data_afastamento.year)
            elif r.mes_referencia:
                ano = r.mes_referencia.split('-')[0]
            
            if not ano:
                continue
            
            if ano not in dados_por_ano:
                dados_por_ano[ano] = 0
            
            dados_por_ano[ano] += r.quantidade or 0
        
        # Converte para lista ordenada
        anos_ordenados = sorted(dados_por_ano.keys())
        
        return [
            {
                'ano': ano,
                'quantidade': dados_por_ano[ano]
            }
            for ano in anos_ordenados
        ]