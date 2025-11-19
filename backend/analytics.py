"""
Analytics - Cálculos de métricas e análises
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, or_
from .models import Atestado, Upload, Client
from datetime import datetime, timedelta
from typing import Dict, List, Any, Union
import calendar
try:
    from dateutil.relativedelta import relativedelta
except ImportError:
    # Fallback simples se dateutil não estiver disponível
    class relativedelta:
        def __init__(self, months=0):
            self.months = months
        def __rsub__(self, other):
            # Implementação simples para subtração
            if isinstance(other, datetime):
                year = other.year
                month = other.month - self.months
                while month <= 0:
                    month += 12
                    year -= 1
                return datetime(year, month, other.day, other.hour, other.minute, other.second)
            return other

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
        # Função para normalizar gênero
        def normalizar_genero(genero_str):
            if not genero_str:
                return None
            genero_str = str(genero_str).strip().upper()
            # Normaliza para M ou F
            if genero_str.startswith('M') or genero_str == 'MASCULINO' or genero_str == 'MALE':
                return 'M'
            elif genero_str.startswith('F') or genero_str == 'FEMININO' or genero_str == 'FEMALE':
                return 'F'
            return None
        
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

        results = query.all()
        
        # Agrupa e normaliza os resultados
        generos_agrupados = {}
        for r in results:
            genero_normalizado = normalizar_genero(r.genero)
            if genero_normalizado:
                if genero_normalizado not in generos_agrupados:
                    generos_agrupados[genero_normalizado] = {
                        'quantidade': 0,
                        'dias_perdidos': 0.0
                    }
                generos_agrupados[genero_normalizado]['quantidade'] += r.quantidade
                generos_agrupados[genero_normalizado]['dias_perdidos'] += float(r.dias_perdidos or 0)
        
        # Retorna lista ordenada: M primeiro, depois F
        resultado = []
        if 'M' in generos_agrupados:
            resultado.append({
                'genero': 'M',
                'quantidade': generos_agrupados['M']['quantidade'],
                'dias_perdidos': round(generos_agrupados['M']['dias_perdidos'], 2)
            })
        if 'F' in generos_agrupados:
            resultado.append({
                'genero': 'F',
                'quantidade': generos_agrupados['F']['quantidade'],
                'dias_perdidos': round(generos_agrupados['F']['dias_perdidos'], 2)
            })
        
        return resultado
    
    def distribuicao_genero_funcionarios(self, client_id: int, mes_inicio: str = None, mes_fim: str = None, funcionario: str = None, setor: str = None) -> List[Dict[str, Any]]:
        """Distribuição de FUNCIONÁRIOS ÚNICOS por gênero"""
        # Função para normalizar gênero
        def normalizar_genero(genero_str):
            if not genero_str:
                return None
            genero_str = str(genero_str).strip().upper()
            # Normaliza para M ou F
            if genero_str.startswith('M') or genero_str == 'MASCULINO' or genero_str == 'MALE':
                return 'M'
            elif genero_str.startswith('F') or genero_str == 'FEMININO' or genero_str == 'FEMALE':
                return 'F'
            return None
        
        # Busca TODOS os registros (não agrupa ainda) para processar em Python
        # Isso garante que pegamos o gênero correto de cada funcionário
        query = self.db.query(
            Atestado.nomecompleto,
            Atestado.genero
        ).join(Upload).filter(
            Upload.client_id == client_id,
            Atestado.nomecompleto != '',
            Atestado.nomecompleto.isnot(None),
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
        
        # Busca todos os registros
        results = query.all()
        
        # Agrupa funcionários únicos por gênero normalizado
        # Usa dict para armazenar o gênero de cada funcionário único
        funcionarios_unicos = {}  # {nome: genero_normalizado}
        
        for r in results:
            nome_func = r.nomecompleto.strip() if r.nomecompleto else None
            if not nome_func:
                continue
                
            genero_normalizado = normalizar_genero(r.genero)
            if genero_normalizado:
                # Se o funcionário já existe, mantém o gênero (assumindo que é o mesmo)
                # Se não existe, adiciona
                if nome_func not in funcionarios_unicos:
                    funcionarios_unicos[nome_func] = genero_normalizado
        
        # Conta funcionários por gênero
        contagem_por_genero = {'M': 0, 'F': 0}
        generos_nao_normalizados = {}  # Para debug
        
        for nome, genero in funcionarios_unicos.items():
            if genero in contagem_por_genero:
                contagem_por_genero[genero] += 1
            else:
                # Debug: coleta gêneros que não foram normalizados
                if genero not in generos_nao_normalizados:
                    generos_nao_normalizados[genero] = 0
                generos_nao_normalizados[genero] += 1
        
        # Log para debug (pode remover depois)
        if generos_nao_normalizados:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Gêneros não normalizados encontrados: {generos_nao_normalizados}")
        
        # Monta resultado
        resultado = []
        if contagem_por_genero['M'] > 0:
            resultado.append({
                'genero': 'M',
                'quantidade': contagem_por_genero['M'],
                'dias_perdidos': 0
            })
        if contagem_por_genero['F'] > 0:
            resultado.append({
                'genero': 'F',
                'quantidade': contagem_por_genero['F'],
                'dias_perdidos': 0
            })
        
        return resultado
    
    def distribuicao_genero_mensal(self, client_id: int, mes_inicio: str = None, mes_fim: str = None, funcionario: str = None, setor: str = None) -> List[Dict[str, Any]]:
        """Distribuição mensal por gênero (atestados)"""
        # Função de normalização reaproveitada
        def normalizar_genero(genero_str):
            if not genero_str:
                return None
            genero_str = str(genero_str).strip().upper()
            if genero_str.startswith('M') or genero_str == 'MASCULINO' or genero_str == 'MALE':
                return 'M'
            if genero_str.startswith('F') or genero_str == 'FEMININO' or genero_str == 'FEMALE':
                return 'F'
            return None
        
        query = self.db.query(
            Upload.mes_referencia.label('mes'),
            Atestado.genero,
            func.count(Atestado.id).label('quantidade'),
            func.sum(Atestado.dias_atestados).label('dias_perdidos'),
            func.sum(Atestado.horas_perdi).label('horas_perdidas')
        ).join(Upload).filter(
            Upload.client_id == client_id,
            Atestado.genero != '',
            Atestado.genero.isnot(None),
            Atestado.nomecompleto != '',
            Atestado.nomecompleto.isnot(None)
        )
        
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        
        from .analytics_helper import aplicar_filtro_funcionario, aplicar_filtro_setor
        query = aplicar_filtro_funcionario(query, funcionario)
        query = aplicar_filtro_setor(query, setor)
        
        query = query.group_by(Upload.mes_referencia, Atestado.genero).order_by(Upload.mes_referencia.asc())
        
        results = query.all()
        
        dados = []
        for r in results:
            genero_normalizado = normalizar_genero(r.genero)
            if not genero_normalizado:
                continue
            dados.append({
                'mes': r.mes,
                'genero': genero_normalizado,
                'quantidade': int(r.quantidade or 0),
                'dias_perdidos': round(float(r.dias_perdidos or 0), 2),
                'horas_perdidas': round(float(r.horas_perdidas or 0), 2)
            })
        
        return dados
    
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
        """Classificação por Funcionário - Roda de Ouro (soma dias de atestados, não conta atestados)"""
        query = self.db.query(
            Atestado.nomecompleto,
            func.sum(Atestado.dias_atestados).label('dias_atestados')
        ).join(Upload).filter(
            Upload.client_id == client_id,
            or_(
                Atestado.nomecompleto != '',
                Atestado.nomecompleto.isnot(None)
            ),
            Atestado.dias_atestados > 0  # Só inclui funcionários com dias de atestados
        )
        
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        
        from .analytics_helper import aplicar_filtro_funcionario, aplicar_filtro_setor
        query = aplicar_filtro_funcionario(query, funcionario)
        query = aplicar_filtro_setor(query, setor)
        
        query = query.group_by(Atestado.nomecompleto).order_by(func.sum(Atestado.dias_atestados).desc()).limit(limit)
        
        results = query.all()
        
        return [
            {
                'nome': r.nomecompleto or 'Não informado',
                'quantidade': float(r.dias_atestados or 0)  # Mantém 'quantidade' para compatibilidade com frontend, mas agora é dias
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
        """Classificação por Doença - Roda de Ouro (soma dias perdidos por nome real da doença) - USA COLUNA 'Doença' DOS DADOS ORIGINAIS"""
        import json
        
        # Busca todos os registros com dados originais
        query = self.db.query(
            Atestado.dados_originais,
            Atestado.dias_atestados
        ).join(Upload).filter(
            Upload.client_id == client_id,
            Atestado.dias_atestados > 0  # Só inclui registros com dias
        )
        
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        
        from .analytics_helper import aplicar_filtro_funcionario, aplicar_filtro_setor
        query = aplicar_filtro_funcionario(query, funcionario)
        query = aplicar_filtro_setor(query, setor)
        
        registros = query.all()
        
        # Agrupa por nome da doença usando coluna "Doença" dos dados originais
        doencas_dict = {}
        registros_sem_nome = 0
        
        for r in registros:
            # Busca coluna "Doença" nos dados originais
            nome_doenca = None
            if r.dados_originais:
                try:
                    dados_orig = json.loads(r.dados_originais)
                    # Prioriza coluna "Doença" (nome exato da coluna na planilha RODA DE OURO)
                    nome_doenca = dados_orig.get('Doença') or dados_orig.get('doença') or dados_orig.get('DOENÇA')
                    if nome_doenca:
                        nome_doenca = str(nome_doenca).strip()
                except:
                    pass
            
            # Fallback: se não encontrou em dados_originais, tenta campos do banco
            if not nome_doenca:
                # Tenta campos do banco como fallback
                atestado_completo = self.db.query(Atestado).filter(Atestado.dados_originais == r.dados_originais).first()
                if atestado_completo:
                    if atestado_completo.descricao_cid and str(atestado_completo.descricao_cid).strip():
                        nome_doenca = str(atestado_completo.descricao_cid).strip()
                    elif atestado_completo.diagnostico and str(atestado_completo.diagnostico).strip():
                        nome_doenca = str(atestado_completo.diagnostico).strip()
                    elif atestado_completo.cid and str(atestado_completo.cid).strip():
                        nome_doenca = str(atestado_completo.cid).strip()
            
            if not nome_doenca:
                registros_sem_nome += 1
                continue
            
            # Normaliza o nome (remove espaços extras, converte para maiúsculas para agrupar)
            nome_doenca_normalizado = ' '.join(nome_doenca.upper().split())
            
            # Agrupa por nome normalizado e soma os dias
            if nome_doenca_normalizado not in doencas_dict:
                doencas_dict[nome_doenca_normalizado] = {
                    'nome_original': nome_doenca,  # Mantém o nome original para exibição
                    'dias': 0
                }
            doencas_dict[nome_doenca_normalizado]['dias'] += float(r.dias_atestados or 0)
        
        print(f"📊 Doenças agrupadas: {len(doencas_dict)}, Registros sem nome: {registros_sem_nome}")
        
        # Ordena por dias perdidos (decrescente) e limita
        doencas_ordenadas = sorted(
            doencas_dict.items(), 
            key=lambda x: x[1]['dias'], 
            reverse=True
        )[:limit]
        
        resultado = [
            {
                'tipo_doenca': item[1]['nome_original'],  # Usa nome original (não normalizado)
                'quantidade': round(item[1]['dias'], 2)  # Dias de afastamento
            }
            for item in doencas_ordenadas
        ]
        
        print(f"✅ Retornando {len(resultado)} doenças ordenadas por dias")
        for item in resultado[:5]:  # Mostra as 5 primeiras
            print(f"  - {item['tipo_doenca']}: {item['quantidade']} dias")
        
        return resultado
    
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
        """Dias atestados por ano com coerência (COERENTE vs SEM COERÊNCIA) - agrupa por ano e mês - USA COLUNAS 'ano', 'mês' E 'coerente' DOS DADOS ORIGINAIS"""
        import json
        from datetime import datetime
        
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
        
        # Agrupa por ano (e depois por mês dentro do ano)
        dados_por_ano = {}
        dados_por_mes_ano = {}  # Para detalhamento mensal
        
        for r in registros:
            # Tenta obter ano e mês dos dados originais (colunas "ano" e "mês")
            ano = None
            mes = None
            mes_ano_key = None
            coerente_valor = None
            
            # Prioridade 1: Busca nos dados originais (colunas "ano" e "mês" da planilha RODA DE OURO)
            if r.dados_originais:
                try:
                    dados_orig = json.loads(r.dados_originais)
                    # Busca colunas "ano" e "mês" (nomes exatos da planilha)
                    ano_str = dados_orig.get('ano') or dados_orig.get('Ano') or dados_orig.get('ANO')
                    mes_str = dados_orig.get('mês') or dados_orig.get('Mês') or dados_orig.get('MÊS') or dados_orig.get('mes')
                    
                    if ano_str:
                        ano = str(ano_str).strip()
                    if mes_str:
                        mes = str(mes_str).strip().zfill(2)
                    
                    # Busca coluna "coerente" dos dados originais
                    coerente_valor = dados_orig.get('coerente') or dados_orig.get('Coerente') or dados_orig.get('COERENTE')
                except:
                    pass
            
            # Prioridade 2: Se não encontrou nos dados originais, usa data_afastamento
            if not ano and r.data_afastamento:
                ano = str(r.data_afastamento.year)
                mes = str(r.data_afastamento.month).zfill(2)
            
            # Prioridade 3: Se ainda não encontrou, usa mes_referencia
            if not ano and r.mes_referencia:
                partes = r.mes_referencia.split('-')
                if len(partes) >= 2:
                    ano = partes[0]
                    mes = partes[1]
                elif len(partes) == 1 and len(partes[0]) == 4:
                    ano = partes[0]
                    mes = '01'
            
            if not ano:
                continue
            
            # Monta chave mês-ano
            if mes:
                mes_ano_key = f"{ano}-{mes}"
            
            # Agrupa por ano
            if ano not in dados_por_ano:
                dados_por_ano[ano] = {'coerente': 0, 'sem_coerencia': 0}
            
            # Agrupa por mês-ano (para detalhamento)
            if mes_ano_key:
                if mes_ano_key not in dados_por_mes_ano:
                    dados_por_mes_ano[mes_ano_key] = {'coerente': 0, 'sem_coerencia': 0}
            
            # Verifica coerência: usa coluna "coerente" dos dados originais se disponível
            if coerente_valor:
                # Usa valor direto da coluna "coerente"
                is_coerente = str(coerente_valor).upper().strip() == 'COERENTE'
            else:
                # Fallback: usa função de verificação
                is_coerente = self._verificar_coerencia(r.dados_originais, r.dias_atestados)
            
            dias = r.dias_atestados or 0
            
            if is_coerente:
                dados_por_ano[ano]['coerente'] += dias
                if mes_ano_key:
                    dados_por_mes_ano[mes_ano_key]['coerente'] += dias
            else:
                dados_por_ano[ano]['sem_coerencia'] += dias
                if mes_ano_key:
                    dados_por_mes_ano[mes_ano_key]['sem_coerencia'] += dias
        
        # Converte para lista ordenada (por ano)
        anos_ordenados = sorted(dados_por_ano.keys())
        
        # Ordena meses dentro de cada ano
        meses_ordenados = sorted(dados_por_mes_ano.keys())
        
        return {
            'anos': anos_ordenados,
            'coerente': [dados_por_ano[ano]['coerente'] for ano in anos_ordenados],
            'sem_coerencia': [dados_por_ano[ano]['sem_coerencia'] for ano in anos_ordenados],
            # Dados mensais para gráfico detalhado
            'meses': meses_ordenados,
            'coerente_mensal': [dados_por_mes_ano[mes]['coerente'] for mes in meses_ordenados],
            'sem_coerencia_mensal': [dados_por_mes_ano[mes]['sem_coerencia'] for mes in meses_ordenados]
        }
    
    def _verificar_coerencia(self, dados_originais_json: str, dias_atestados: float) -> bool:
        """Verifica se o atestado é coerente baseado nos dados originais - USA COLUNA 'coerente' DOS DADOS ORIGINAIS"""
        import json
        
        if not dados_originais_json:
            # Se não tem dados originais, assume SEM coerência (mais conservador)
            return False
        
        try:
            dados_originais = json.loads(dados_originais_json)
            
            # PRIORIDADE 1: Busca coluna "coerente" (nome exato da coluna na planilha RODA DE OURO)
            coerente_valor = dados_originais.get('coerente') or dados_originais.get('Coerente') or dados_originais.get('COERENTE')
            if coerente_valor:
                valor_str = str(coerente_valor).upper().strip()
                if valor_str == 'COERENTE':
                    return True
                elif 'SEM COER' in valor_str or 'SEM_COER' in valor_str or 'SEMCOER' in valor_str:
                    return False
                elif 'NÃO' in valor_str or 'NAO' in valor_str or 'N' in valor_str or 'FALSE' in valor_str or '0' in valor_str:
                    return False
                else:
                    return True  # Se tem valor mas não é claramente negativo, assume coerente
            
            # PRIORIDADE 2: Busca em "Parecer Médico" (pode conter "COERENTE" ou "SEM COERÊNCIA")
            parecer = dados_originais.get('Parecer Médico') or dados_originais.get('Parecer Medico') or dados_originais.get('PAREcer Médico')
            if parecer:
                parecer_str = str(parecer).upper()
                if 'COERENTE' in parecer_str and 'SEM COER' not in parecer_str:
                    return True
                elif 'SEM COER' in parecer_str:
                    return False
            
            # PRIORIDADE 3: Procura campos relacionados a coerência (fallback)
            for key, value in dados_originais.items():
                key_upper = str(key).upper()
                value_str = str(value).upper() if value else ''
                
                # Verifica se tem campo "SEM COERÊNCIA" primeiro (tem prioridade)
                if 'SEM COER' in key_upper or 'SEM_COER' in key_upper or 'SEMCOER' in key_upper:
                    if 'SIM' in value_str or 'S' in value_str or 'TRUE' in value_str or '1' in value_str:
                        return False  # SEM coerência
                    elif 'NÃO' in value_str or 'NAO' in value_str or 'N' in value_str or 'FALSE' in value_str or '0' in value_str:
                        return True  # NÃO tem sem coerência = coerente
                
                # Verifica se tem campo de coerência
                if 'COERENTE' in key_upper or 'COERENCIA' in key_upper:
                    if 'SIM' in value_str or 'S' in value_str or 'TRUE' in value_str or '1' in value_str:
                        return True  # COERENTE
                    elif 'NÃO' in value_str or 'NAO' in value_str or 'N' in value_str or 'FALSE' in value_str or '0' in value_str:
                        return False  # NÃO coerente = sem coerência
            
            # Se não encontrou campo de coerência, assume SEM coerência por padrão (mais conservador)
            return False
        except:
            # Se der erro ao parsear, assume SEM coerência (mais conservador)
            return False
    
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
        """Tempo de Serviço x Atestados - USA COLUNA 'Admissão' DOS DADOS ORIGINAIS - Analisa se funcionários mais antigos ou mais novos dão mais atestados"""
        import json
        from datetime import datetime, date
        
        query = self.db.query(
            Atestado.dados_originais,
            Atestado.dias_atestados,
            Atestado.nomecompleto
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
        
        # Função para calcular tempo de serviço em anos
        def calcular_tempo_servico(data_admissao_str):
            """Calcula tempo de serviço em anos a partir da data de admissão"""
            if not data_admissao_str:
                return None
            
            try:
                # Tenta vários formatos de data
                data_admissao = None
                if isinstance(data_admissao_str, str):
                    # Tenta formato DD/MM/YYYY
                    try:
                        data_admissao = datetime.strptime(data_admissao_str, '%d/%m/%Y').date()
                    except:
                        # Tenta formato YYYY-MM-DD
                        try:
                            data_admissao = datetime.strptime(data_admissao_str, '%Y-%m-%d').date()
                        except:
                            # Tenta formato DD-MM-YYYY
                            try:
                                data_admissao = datetime.strptime(data_admissao_str, '%d-%m-%Y').date()
                            except:
                                # Tenta apenas ano (YYYY)
                                try:
                                    ano = int(data_admissao_str[:4])
                                    data_admissao = date(ano, 1, 1)
                                except:
                                    pass
                
                if not data_admissao:
                    return None
                
                # Calcula diferença em anos
                hoje = date.today()
                anos = (hoje - data_admissao).days / 365.25
                return anos
            except:
                return None
        
        # Função para categorizar tempo de serviço em faixas
        def categorizar_tempo_servico(anos):
            """Categoriza tempo de serviço em faixas"""
            if anos is None:
                return 'Não informado'
            elif anos < 1:
                return '0-1 ano'
            elif anos < 3:
                return '1-3 anos'
            elif anos < 5:
                return '3-5 anos'
            elif anos < 10:
                return '5-10 anos'
            else:
                return '10+ anos'
        
        # Agrupa por faixa de tempo de serviço
        dados_por_faixa = {}
        
        for r in registros:
            # Busca coluna "Admissão" nos dados originais
            data_admissao_str = None
            if r.dados_originais:
                try:
                    dados_orig = json.loads(r.dados_originais)
                    # Busca coluna "Admissão" (nome exato da planilha RODA DE OURO)
                    data_admissao_str = dados_orig.get('Admissão') or dados_orig.get('admissão') or dados_orig.get('ADMISSÃO') or dados_orig.get('Admissao')
                except:
                    pass
            
            # Calcula tempo de serviço
            anos_servico = calcular_tempo_servico(data_admissao_str)
            faixa = categorizar_tempo_servico(anos_servico)
            
            # Agrupa por faixa e soma dias de afastamento
            if faixa not in dados_por_faixa:
                dados_por_faixa[faixa] = {
                    'faixa': faixa,
                    'dias_afastamento': 0,
                    'quantidade_atestados': 0
                }
            
            dias = r.dias_atestados or 0
            dados_por_faixa[faixa]['dias_afastamento'] += dias
            dados_por_faixa[faixa]['quantidade_atestados'] += 1
        
        # Ordena faixas por ordem lógica
        ordem_faixas = ['0-1 ano', '1-3 anos', '3-5 anos', '5-10 anos', '10+ anos', 'Não informado']
        resultado = []
        for faixa_ordem in ordem_faixas:
            if faixa_ordem in dados_por_faixa:
                resultado.append({
                    'faixa_tempo_servico': dados_por_faixa[faixa_ordem]['faixa'],
                    'dias_afastamento': round(dados_por_faixa[faixa_ordem]['dias_afastamento'], 2),
                    'quantidade_atestados': dados_por_faixa[faixa_ordem]['quantidade_atestados']
                })
        
        # Adiciona outras faixas que não estão na ordem padrão (se houver)
        for faixa, dados in dados_por_faixa.items():
            if faixa not in ordem_faixas:
                resultado.append({
                    'faixa_tempo_servico': dados['faixa'],
                    'dias_afastamento': round(dados['dias_afastamento'], 2),
                    'quantidade_atestados': dados['quantidade_atestados']
                })
        
        print(f"📊 Tempo Serviço x Atestados - {len(resultado)} faixas encontradas")
        for item in resultado:
            print(f"  - {item['faixa_tempo_servico']}: {item['dias_afastamento']} dias ({item['quantidade_atestados']} atestados)")
        
        return resultado
    
    def horas_perdidas_por_genero(self, client_id: int, mes_inicio: str = None, mes_fim: str = None, funcionario: str = None, setor: str = None) -> List[Dict[str, Any]]:
        """Horas perdidas por gênero (calcula se horas_perdi estiver zerado)"""
        # Calcula horas: se horas_perdi > 0 usa ele, senão calcula dias_atestados * horas_dia
        query = self.db.query(
            Atestado.genero,
            func.sum(Atestado.horas_perdi).label('horas_perdi_sum'),
            func.sum(Atestado.dias_atestados).label('dias_atestados_sum'),
            func.sum(Atestado.horas_dia).label('horas_dia_sum'),
            func.count(Atestado.id).label('quantidade'),
            func.sum(Atestado.dias_atestados * Atestado.horas_dia).label('horas_calculadas')
        ).join(Upload).filter(
            Upload.client_id == client_id,
            Atestado.genero != '',
            Atestado.genero.isnot(None)
        )
        
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        
        from .analytics_helper import aplicar_filtro_funcionario, aplicar_filtro_setor
        query = aplicar_filtro_funcionario(query, funcionario)
        query = aplicar_filtro_setor(query, setor)
        
        query = query.group_by(Atestado.genero)
        
        results = query.all()
        
        # Considerando semana = 44 horas
        SEMANA_HORAS = 44
        
        resultado = []
        for r in results:
            # Se horas_perdi tem valor, usa ele, senão calcula
            horas_perdidas = float(r.horas_perdi_sum or 0)
            if horas_perdidas == 0:
                # Calcula: dias * horas_dia (média)
                dias_total = float(r.dias_atestados_sum or 0)
                horas_dia_media = float(r.horas_dia_sum or 0) / float(r.quantidade or 1) if r.quantidade > 0 else 0
                if horas_dia_media == 0:
                    # Tenta usar horas_calculadas se disponível
                    horas_perdidas = float(r.horas_calculadas or 0)
                else:
                    horas_perdidas = dias_total * horas_dia_media
            
            semanas_perdidas = horas_perdidas / SEMANA_HORAS if SEMANA_HORAS > 0 else 0
            
            genero_nome = 'Masculino' if r.genero == 'M' else 'Feminino' if r.genero == 'F' else r.genero
            
            resultado.append({
                'genero': r.genero or '-',
                'genero_label': genero_nome,
                'horas_perdidas': round(horas_perdidas, 2),
                'semanas_perdidas': round(semanas_perdidas, 2),
                'dias_perdidos': round(float(r.dias_atestados_sum or 0), 2),
                'quantidade': r.quantidade or 0
            })
        
        return resultado
    
    def horas_perdidas_por_setor(self, client_id: int, limit: int = 10, mes_inicio: str = None, mes_fim: str = None, funcionario: str = None, setor: str = None) -> List[Dict[str, Any]]:
        """Horas perdidas por setor (calcula se horas_perdi estiver zerado)"""
        query = self.db.query(
            Atestado.setor,
            func.sum(Atestado.horas_perdi).label('horas_perdi_sum'),
            func.sum(Atestado.dias_atestados).label('dias_atestados_sum'),
            func.avg(Atestado.horas_dia).label('horas_dia_media'),
            func.count(Atestado.id).label('quantidade'),
            func.sum(Atestado.dias_atestados * Atestado.horas_dia).label('horas_calculadas')
        ).join(Upload).filter(
            Upload.client_id == client_id,
            Atestado.setor != '',
            Atestado.setor.isnot(None)
        )
        
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        
        from .analytics_helper import aplicar_filtro_funcionario, aplicar_filtro_setor
        query = aplicar_filtro_funcionario(query, funcionario)
        # Não aplica filtro de setor aqui, pois queremos ver todos os setores
        
        query = query.group_by(Atestado.setor).order_by(func.sum(Atestado.horas_perdi).desc()).limit(limit)
        
        results = query.all()
        
        # Considerando semana = 44 horas
        SEMANA_HORAS = 44
        
        resultado = []
        for r in results:
            # Se horas_perdi tem valor, usa ele, senão calcula
            horas_perdidas = float(r.horas_perdi_sum or 0)
            if horas_perdidas == 0:
                # Calcula: dias * horas_dia (média)
                dias_total = float(r.dias_atestados_sum or 0)
                horas_dia_media = float(r.horas_dia_media or 0)
                if horas_dia_media == 0:
                    # Tenta usar horas_calculadas se disponível
                    horas_perdidas = float(r.horas_calculadas or 0)
                else:
                    horas_perdidas = dias_total * horas_dia_media
            
            semanas_perdidas = horas_perdidas / SEMANA_HORAS if SEMANA_HORAS > 0 else 0
            
            resultado.append({
                'setor': r.setor or 'Não informado',
                'horas_perdidas': round(horas_perdidas, 2),
                'semanas_perdidas': round(semanas_perdidas, 2),
                'dias_perdidos': round(float(r.dias_atestados_sum or 0), 2),
                'quantidade': r.quantidade or 0
            })
        
        return resultado
    
    def evolucao_mensal_horas(self, client_id: int, meses: int = 12, mes_inicio: str = None, mes_fim: str = None, funcionario: str = None, setor: str = None) -> List[Dict[str, Any]]:
        """Evolução mensal de horas perdidas - MESMO RACIOCÍNIO DE dias_atestados_por_ano_coerencia: agrupa mês a mês"""
        import json
        from datetime import datetime
        
        # Busca todos os registros (mesmo padrão de dias_atestados_por_ano_coerencia)
        query = self.db.query(
            Atestado.horas_perdi,
            Atestado.dias_atestados,
            Atestado.horas_dia,
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
        
        # Agrupa por mês-ano (mesmo padrão de dias_atestados_por_ano_coerencia)
        dados_por_mes_ano = {}  # Chave: "YYYY-MM", Valor: {horas_perdidas, semanas_perdidas, dias_perdidos, quantidade}
        
        # Considerando semana = 44 horas
        SEMANA_HORAS = 44
        
        for r in registros:
            # Tenta obter ano e mês dos dados originais (colunas "ano" e "mês") - MESMO PADRÃO
            ano = None
            mes = None
            mes_ano_key = None
            
            # Prioridade 1: Busca nos dados originais (colunas "ano" e "mês" da planilha)
            if r.dados_originais:
                try:
                    dados_orig = json.loads(r.dados_originais)
                    # Busca colunas "ano" e "mês" (nomes exatos da planilha)
                    ano_str = dados_orig.get('ano') or dados_orig.get('Ano') or dados_orig.get('ANO')
                    mes_str = dados_orig.get('mês') or dados_orig.get('Mês') or dados_orig.get('MÊS') or dados_orig.get('mes')
                    
                    if ano_str:
                        ano = str(ano_str).strip()
                    if mes_str:
                        mes = str(mes_str).strip().zfill(2)
                except:
                    pass
            
            # Prioridade 2: Se não encontrou nos dados originais, usa data_afastamento
            if not ano and r.data_afastamento:
                ano = str(r.data_afastamento.year)
                mes = str(r.data_afastamento.month).zfill(2)
            
            # Prioridade 3: Se ainda não encontrou, usa mes_referencia
            if not ano and r.mes_referencia:
                partes = r.mes_referencia.split('-')
                if len(partes) >= 2:
                    ano = partes[0]
                    mes = partes[1]
                elif len(partes) == 1 and len(partes[0]) == 4:
                    ano = partes[0]
                    mes = '01'
            
            if not ano:
                continue
            
            # Monta chave mês-ano (formato "YYYY-MM")
            if mes:
                mes_ano_key = f"{ano}-{mes}"
            else:
                mes_ano_key = f"{ano}-01"  # Fallback para janeiro se não tiver mês
            
            # Inicializa estrutura para este mês-ano se não existir
            if mes_ano_key not in dados_por_mes_ano:
                dados_por_mes_ano[mes_ano_key] = {
                    'horas_perdidas': 0.0,
                    'semanas_perdidas': 0.0,
                    'dias_perdidos': 0.0,
                    'quantidade': 0
                }
            
            # Calcula horas perdidas: se horas_perdi tem valor, usa ele, senão calcula
            horas_perdidas = float(r.horas_perdi or 0)
            if horas_perdidas == 0:
                # Calcula: dias * horas_dia
                dias_total = float(r.dias_atestados or 0)
                horas_dia_valor = float(r.horas_dia or 0)
                if horas_dia_valor > 0:
                    horas_perdidas = dias_total * horas_dia_valor
            
            semanas_perdidas = horas_perdidas / SEMANA_HORAS if SEMANA_HORAS > 0 else 0
            dias_perdidos = float(r.dias_atestados or 0)
            
            # Acumula valores para este mês-ano
            dados_por_mes_ano[mes_ano_key]['horas_perdidas'] += horas_perdidas
            dados_por_mes_ano[mes_ano_key]['semanas_perdidas'] += semanas_perdidas
            dados_por_mes_ano[mes_ano_key]['dias_perdidos'] += dias_perdidos
            dados_por_mes_ano[mes_ano_key]['quantidade'] += 1
        
        # Ordena meses (mesmo padrão de dias_atestados_por_ano_coerencia)
        meses_ordenados = sorted(dados_por_mes_ano.keys())
        
        # Converte para lista de dicionários (mesmo formato esperado pelo frontend)
        dados = []
        for mes_ano in meses_ordenados:
            dados_mes = dados_por_mes_ano[mes_ano]
            dados.append({
                'mes': mes_ano,
                'horas_perdidas': round(dados_mes['horas_perdidas'], 2),
                'semanas_perdidas': round(dados_mes['semanas_perdidas'], 2),
                'dias_perdidos': round(dados_mes['dias_perdidos'], 2),
                'quantidade': dados_mes['quantidade']
            })
        
        # Já está ordenado crescente (do mais antigo para o mais recente) - MESMO PADRÃO
        return dados
    
    def comparativo_periodos(self, client_id: int, tipo_comparacao: str = 'mes', funcionario: str = None, setor: str = None) -> Dict[str, Any]:
        """
        Comparativo entre períodos (mês atual vs anterior, trimestre atual vs anterior)
        tipo_comparacao: 'mes' ou 'trimestre'
        """
        hoje = datetime.now()
        
        if tipo_comparacao == 'mes':
            # Mês atual
            mes_atual = hoje.strftime('%Y-%m')
            # Mês anterior
            mes_anterior_date = hoje - relativedelta(months=1)
            mes_anterior = mes_anterior_date.strftime('%Y-%m')
            
            # Calcula métricas do mês atual
            metricas_atual = self.metricas_gerais(client_id, mes_inicio=mes_atual, mes_fim=mes_atual, funcionario=funcionario, setor=setor)
            
            # Calcula métricas do mês anterior
            metricas_anterior = self.metricas_gerais(client_id, mes_inicio=mes_anterior, mes_fim=mes_anterior, funcionario=funcionario, setor=setor)
            
            # Calcula variação percentual
            def calcular_variacao(atual, anterior):
                if anterior == 0:
                    return 100.0 if atual > 0 else 0.0
                return ((atual - anterior) / anterior) * 100
            
            variacao_dias = calcular_variacao(metricas_atual.get('total_dias', 0), metricas_anterior.get('total_dias', 0))
            variacao_horas = calcular_variacao(metricas_atual.get('total_horas', 0), metricas_anterior.get('total_horas', 0))
            variacao_registros = calcular_variacao(metricas_atual.get('total_registros', 0), metricas_anterior.get('total_registros', 0))
            
            return {
                'tipo': 'mes',
                'periodo_atual': {
                    'mes': mes_atual,
                    'label': hoje.strftime('%B/%Y'),
                    'dias_perdidos': round(metricas_atual.get('total_dias', 0), 2),
                    'horas_perdidas': round(metricas_atual.get('total_horas', 0), 2),
                    'total_registros': metricas_atual.get('total_registros', 0)
                },
                'periodo_anterior': {
                    'mes': mes_anterior,
                    'label': mes_anterior_date.strftime('%B/%Y'),
                    'dias_perdidos': round(metricas_anterior.get('total_dias', 0), 2),
                    'horas_perdidas': round(metricas_anterior.get('total_horas', 0), 2),
                    'total_registros': metricas_anterior.get('total_registros', 0)
                },
                'variacao': {
                    'dias_perdidos': round(variacao_dias, 2),
                    'horas_perdidas': round(variacao_horas, 2),
                    'total_registros': round(variacao_registros, 2)
                }
            }
        
        elif tipo_comparacao == 'trimestre':
            # Trimestre atual (últimos 3 meses)
            mes_fim_trimestre = hoje.strftime('%Y-%m')
            mes_inicio_trimestre_date = hoje - relativedelta(months=2)
            mes_inicio_trimestre = mes_inicio_trimestre_date.strftime('%Y-%m')
            
            # Trimestre anterior (3 meses antes)
            mes_fim_anterior_date = hoje - relativedelta(months=3)
            mes_fim_anterior = mes_fim_anterior_date.strftime('%Y-%m')
            mes_inicio_anterior_date = hoje - relativedelta(months=5)
            mes_inicio_anterior = mes_inicio_anterior_date.strftime('%Y-%m')
            
            # Calcula métricas do trimestre atual
            metricas_atual = self.metricas_gerais(client_id, mes_inicio=mes_inicio_trimestre, mes_fim=mes_fim_trimestre, funcionario=funcionario, setor=setor)
            
            # Calcula métricas do trimestre anterior
            metricas_anterior = self.metricas_gerais(client_id, mes_inicio=mes_inicio_anterior, mes_fim=mes_fim_anterior, funcionario=funcionario, setor=setor)
            
            # Calcula variação percentual
            def calcular_variacao(atual, anterior):
                if anterior == 0:
                    return 100.0 if atual > 0 else 0.0
                return ((atual - anterior) / anterior) * 100
            
            variacao_dias = calcular_variacao(metricas_atual.get('total_dias', 0), metricas_anterior.get('total_dias', 0))
            variacao_horas = calcular_variacao(metricas_atual.get('total_horas', 0), metricas_anterior.get('total_horas', 0))
            variacao_registros = calcular_variacao(metricas_atual.get('total_registros', 0), metricas_anterior.get('total_registros', 0))
            
            return {
                'tipo': 'trimestre',
                'periodo_atual': {
                    'mes_inicio': mes_inicio_trimestre,
                    'mes_fim': mes_fim_trimestre,
                    'label': f"{mes_inicio_trimestre_date.strftime('%b/%Y')} a {hoje.strftime('%b/%Y')}",
                    'dias_perdidos': round(metricas_atual.get('total_dias', 0), 2),
                    'horas_perdidas': round(metricas_atual.get('total_horas', 0), 2),
                    'total_registros': metricas_atual.get('total_registros', 0)
                },
                'periodo_anterior': {
                    'mes_inicio': mes_inicio_anterior,
                    'mes_fim': mes_fim_anterior,
                    'label': f"{mes_inicio_anterior_date.strftime('%b/%Y')} a {mes_fim_anterior_date.strftime('%b/%Y')}",
                    'dias_perdidos': round(metricas_anterior.get('total_dias', 0), 2),
                    'horas_perdidas': round(metricas_anterior.get('total_horas', 0), 2),
                    'total_registros': metricas_anterior.get('total_registros', 0)
                },
                'variacao': {
                    'dias_perdidos': round(variacao_dias, 2),
                    'horas_perdidas': round(variacao_horas, 2),
                    'total_registros': round(variacao_registros, 2)
                }
            }
        
        else:
            raise ValueError(f"Tipo de comparação inválido: {tipo_comparacao}. Use 'mes' ou 'trimestre'")
    
    def analise_detalhada_genero(self, client_id: int, mes_inicio: str = None, mes_fim: str = None, funcionario: str = None, setor: str = None) -> Dict[str, Any]:
        """Análise detalhada por gênero (dias, horas, percentuais, comparações)"""
        # Busca dados por gênero
        generos_data = self.horas_perdidas_por_genero(client_id, mes_inicio, mes_fim, funcionario, setor)
        
        # Busca totais gerais
        metricas = self.metricas_gerais(client_id, mes_inicio, mes_fim, funcionario, setor)
        
        total_dias = metricas.get('total_dias_perdidos', 0)
        total_registros = metricas.get('total_atestados', 0)
        
        # Calcula totais de horas
        total_horas = 0
        for g in generos_data:
            total_horas += g.get('horas_perdidas', 0)
        
        # Calcula percentuais
        resultado = {
            'total_dias': total_dias,
            'total_horas': round(total_horas, 2),
            'total_registros': total_registros,
            'generos': []
        }
        
        for g in generos_data:
            pct_dias = (g.get('dias_perdidos', 0) / total_dias * 100) if total_dias > 0 else 0
            pct_horas = (g.get('horas_perdidas', 0) / total_horas * 100) if total_horas > 0 else 0
            pct_registros = (g.get('quantidade', 0) / total_registros * 100) if total_registros > 0 else 0
            
            resultado['generos'].append({
                **g,
                'percentual_dias': round(pct_dias, 2),
                'percentual_horas': round(pct_horas, 2),
                'percentual_registros': round(pct_registros, 2)
            })
        
        return resultado
    
    def comparativo_dias_horas_genero(self, client_id: int, mes_inicio: str = None, mes_fim: str = None, funcionario: str = None, setor: str = None) -> List[Dict[str, Any]]:
        """Comparativo de dias vs horas perdidas por gênero"""
        generos_data = self.horas_perdidas_por_genero(client_id, mes_inicio, mes_fim, funcionario, setor)
        
        resultado = []
        for g in generos_data:
            resultado.append({
                'genero': g.get('genero'),
                'genero_label': g.get('genero_label'),
                'dias_perdidos': g.get('dias_perdidos', 0),
                'horas_perdidas': g.get('horas_perdidas', 0),
                'semanas_perdidas': g.get('semanas_perdidas', 0),
                'quantidade': g.get('quantidade', 0)
            })
        
        return resultado
    
    def horas_perdidas_setor_genero(self, client_id: int, mes_inicio: str = None, mes_fim: str = None, funcionario: str = None, setor: str = None) -> List[Dict[str, Any]]:
        """Horas perdidas por setor e gênero (cruzamento)"""
        query = self.db.query(
            Atestado.setor,
            Atestado.genero,
            func.sum(Atestado.horas_perdi).label('horas_perdi_sum'),
            func.sum(Atestado.dias_atestados).label('dias_atestados_sum'),
            func.avg(Atestado.horas_dia).label('horas_dia_media'),
            func.count(Atestado.id).label('quantidade'),
            func.sum(Atestado.dias_atestados * Atestado.horas_dia).label('horas_calculadas')
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
        
        from .analytics_helper import aplicar_filtro_funcionario, aplicar_filtro_setor
        query = aplicar_filtro_funcionario(query, funcionario)
        query = aplicar_filtro_setor(query, setor)
        
        query = query.group_by(Atestado.setor, Atestado.genero).order_by(Atestado.setor, Atestado.genero)
        
        results = query.all()
        
        # Considerando semana = 44 horas
        SEMANA_HORAS = 44
        
        resultado = []
        for r in results:
            # Se horas_perdi tem valor, usa ele, senão calcula
            horas_perdidas = float(r.horas_perdi_sum or 0)
            if horas_perdidas == 0:
                # Calcula: dias * horas_dia (média)
                dias_total = float(r.dias_atestados_sum or 0)
                horas_dia_media = float(r.horas_dia_media or 0)
                if horas_dia_media == 0:
                    # Tenta usar horas_calculadas se disponível
                    horas_perdidas = float(r.horas_calculadas or 0)
                else:
                    horas_perdidas = dias_total * horas_dia_media
            
            semanas_perdidas = horas_perdidas / SEMANA_HORAS if SEMANA_HORAS > 0 else 0
            
            genero_nome = 'Masculino' if r.genero == 'M' else 'Feminino' if r.genero == 'F' else r.genero
            
            resultado.append({
                'setor': r.setor or 'Não informado',
                'genero': r.genero or '-',
                'genero_label': genero_nome,
                'horas_perdidas': round(horas_perdidas, 2),
                'semanas_perdidas': round(semanas_perdidas, 2),
                'dias_perdidos': round(float(r.dias_atestados_sum or 0), 2),
                'quantidade': r.quantidade or 0
            })
        
        return resultado
    
    def taxa_absenteismo_mensal(self, client_id: int, mes_inicio: str = None, mes_fim: str = None, funcionario: str = None, setor: str = None) -> List[Dict[str, Any]]:
        """
        Calcula taxa de absenteísmo mensal (%)
        Taxa = (Dias Perdidos / (Funcionários Únicos * Dias Úteis)) * 100
        Assume 22 dias úteis por mês como padrão
        """
        # Busca evolução mensal (já tem dias perdidos por mês)
        evolucao = self.evolucao_mensal(client_id, mes_inicio, mes_fim, funcionario, setor)
        
        resultado = []
        dias_uteis_padrao = 22  # Média de dias úteis por mês
        
        for item in evolucao:
            mes_ref = item.get('mes')
            dias_perdidos = item.get('dias_perdidos', 0)
            
            # Conta funcionários únicos neste mês específico
            funcionarios_query = self.db.query(
                func.count(func.distinct(Atestado.nomecompleto))
            ).join(Upload).filter(
                Upload.client_id == client_id,
                Upload.mes_referencia == mes_ref
            )
            
            # Aplica filtros usando helper
            from .analytics_helper import aplicar_filtro_funcionario, aplicar_filtro_setor
            funcionarios_query = aplicar_filtro_funcionario(funcionarios_query, funcionario)
            funcionarios_query = aplicar_filtro_setor(funcionarios_query, setor)
            
            num_funcionarios = funcionarios_query.scalar() or 0
            
            # Calcula taxa de absenteísmo
            # Taxa = (Dias Perdidos / (Funcionários * Dias Úteis)) * 100
            if num_funcionarios > 0:
                taxa = (dias_perdidos / (num_funcionarios * dias_uteis_padrao)) * 100
            else:
                taxa = 0.0
            
            resultado.append({
                'mes': mes_ref,
                'mes_label': item.get('mes_label'),
                'dias_perdidos': dias_perdidos,
                'horas_perdidas': item.get('horas_perdidas', 0),
                'funcionarios': num_funcionarios,
                'taxa_absenteismo': round(taxa, 2),
                'quantidade_atestados': item.get('quantidade', 0)
            })
        
        return resultado
    
    def comparativo_ano_anterior(self, client_id: int, mes_inicio: str = None, mes_fim: str = None, funcionario: str = None, setor: str = None) -> List[Dict[str, Any]]:
        """
        Compara período atual com mesmo período do ano anterior
        Retorna dados mês a mês com valores atuais e do ano anterior
        """
        if not mes_inicio or not mes_fim:
            # Se não fornecidos, usa últimos 12 meses
            hoje = datetime.now()
            mes_fim = hoje.strftime('%Y-%m')
            mes_inicio = (hoje - relativedelta(months=11)).strftime('%Y-%m')
        
        # Busca dados do período atual
        evolucao_atual = self.evolucao_mensal(client_id, mes_inicio, mes_fim, funcionario, setor)
        
        # Calcula período do ano anterior
        inicio_date = datetime.strptime(mes_inicio + '-01', '%Y-%m-%d')
        fim_date = datetime.strptime(mes_fim + '-01', '%Y-%m-%d')
        
        mes_inicio_anterior = (inicio_date - relativedelta(years=1)).strftime('%Y-%m')
        mes_fim_anterior = (fim_date - relativedelta(years=1)).strftime('%Y-%m')
        
        # Busca dados do ano anterior
        evolucao_anterior = self.evolucao_mensal(client_id, mes_inicio_anterior, mes_fim_anterior, funcionario, setor)
        
        # Cria mapa de dados do ano anterior por mês relativo
        mapa_anterior = {}
        for item in evolucao_anterior:
            mes_date = datetime.strptime(item['mes'] + '-01', '%Y-%m-%d')
            mes_relativo = mes_date.strftime('%m')  # Apenas o mês (01-12)
            mapa_anterior[mes_relativo] = item
        
        # Combina dados
        resultado = []
        for item_atual in evolucao_atual:
            mes_date = datetime.strptime(item_atual['mes'] + '-01', '%Y-%m-%d')
            mes_relativo = mes_date.strftime('%m')
            
            item_anterior = mapa_anterior.get(mes_relativo, {})
            
            dias_atual = item_atual.get('dias_perdidos', 0)
            dias_anterior = item_anterior.get('dias_perdidos', 0)
            horas_atual = item_atual.get('horas_perdidas', 0)
            horas_anterior = item_anterior.get('horas_perdidas', 0)
            
            # Calcula variação
            variacao_dias = ((dias_atual - dias_anterior) / dias_anterior * 100) if dias_anterior > 0 else (100 if dias_atual > 0 else 0)
            variacao_horas = ((horas_atual - horas_anterior) / horas_anterior * 100) if horas_anterior > 0 else (100 if horas_atual > 0 else 0)
            
            resultado.append({
                'mes': item_atual['mes'],
                'mes_label': item_atual.get('mes_label', ''),
                'ano_atual': {
                    'dias_perdidos': dias_atual,
                    'horas_perdidas': horas_atual,
                    'quantidade': item_atual.get('quantidade', 0)
                },
                'ano_anterior': {
                    'dias_perdidos': dias_anterior,
                    'horas_perdidas': horas_anterior,
                    'quantidade': item_anterior.get('quantidade', 0),
                    'mes_referencia': item_anterior.get('mes', '')
                },
                'variacao': {
                    'dias_percentual': round(variacao_dias, 2),
                    'horas_percentual': round(variacao_horas, 2),
                    'dias_absoluta': round(dias_atual - dias_anterior, 2),
                    'horas_absoluta': round(horas_atual - horas_anterior, 2)
                }
            })
        
        return resultado
    
    def analise_sazonalidade(self, client_id: int, funcionario: str = None, setor: str = None) -> List[Dict[str, Any]]:
        """
        Analisa sazonalidade calculando médias por mês do ano (Jan, Fev, Mar...)
        Agrupa todos os anos disponíveis e calcula média para cada mês
        """
        # Busca TODOS os dados históricos
        evolucao = self.evolucao_mensal(client_id, None, None, funcionario, setor)
        
        # Agrupa por mês do ano (01-12)
        mapa_meses = {}
        for item in evolucao:
            mes_date = datetime.strptime(item['mes'] + '-01', '%Y-%m-%d')
            mes_nome = mes_date.strftime('%B')  # Nome do mês em inglês
            mes_numero = mes_date.strftime('%m')  # 01-12
            
            # Traduz nome do mês
            nomes_pt = {
                'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março',
                'April': 'Abril', 'May': 'Maio', 'June': 'Junho',
                'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro',
                'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'
            }
            mes_nome_pt = nomes_pt.get(mes_nome, mes_nome)
            
            if mes_numero not in mapa_meses:
                mapa_meses[mes_numero] = {
                    'mes': mes_numero,
                    'mes_nome': mes_nome_pt,
                    'dias_total': 0,
                    'horas_total': 0,
                    'quantidade_total': 0,
                    'contagem': 0
                }
            
            mapa_meses[mes_numero]['dias_total'] += item.get('dias_perdidos', 0)
            mapa_meses[mes_numero]['horas_total'] += item.get('horas_perdidas', 0)
            mapa_meses[mes_numero]['quantidade_total'] += item.get('quantidade', 0)
            mapa_meses[mes_numero]['contagem'] += 1
        
        # Calcula médias
        resultado = []
        for mes_numero in sorted(mapa_meses.keys()):
            dados = mapa_meses[mes_numero]
            contagem = dados['contagem']
            
            if contagem > 0:
                resultado.append({
                    'mes': mes_numero,
                    'mes_nome': dados['mes_nome'],
                    'media_dias': round(dados['dias_total'] / contagem, 2),
                    'media_horas': round(dados['horas_total'] / contagem, 2),
                    'media_quantidade': round(dados['quantidade_total'] / contagem, 2),
                    'anos_analisados': contagem,
                    'total_dias': round(dados['dias_total'], 2),
                    'total_horas': round(dados['horas_total'], 2),
                    'total_quantidade': dados['quantidade_total']
                })
        
        return resultado
    
    def heatmap_setores_meses(self, client_id: int, mes_inicio: str = None, mes_fim: str = None, funcionario: str = None) -> Dict[str, Any]:
        """
        Gera dados para heatmap: Setores (linhas) x Meses (colunas) = Dias Perdidos
        Retorna estrutura pronta para renderização de matriz de calor
        """
        # Query: agrupa por setor e mês
        query = self.db.query(
            Atestado.setor,
            Upload.mes_referencia,
            func.sum(Atestado.dias_atestados).label('dias_perdidos')
        ).join(Upload).filter(
            Upload.client_id == client_id
        ).group_by(
            Atestado.setor,
            Upload.mes_referencia
        )
        
        # Filtros
        if mes_inicio:
            query = query.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query = query.filter(Upload.mes_referencia <= mes_fim)
        
        from .analytics_helper import aplicar_filtro_funcionario
        query = aplicar_filtro_funcionario(query, funcionario)
        
        resultados = query.all()
        
        # Monta estrutura: {setor: {mes: dias}}
        mapa_setores = {}
        meses_unicos = set()
        
        for r in resultados:
            setor = r.setor or 'Não informado'
            mes = r.mes_referencia
            dias = float(r.dias_perdidos or 0)
            
            if setor not in mapa_setores:
                mapa_setores[setor] = {}
            
            mapa_setores[setor][mes] = dias
            meses_unicos.add(mes)
        
        # Ordena meses cronologicamente
        meses_ordenados = sorted(list(meses_unicos))
        
        # Prepara dados para heatmap
        setores = sorted(list(mapa_setores.keys()))
        dados_matriz = []
        
        for setor in setores:
            linha = []
            for mes in meses_ordenados:
                valor = mapa_setores[setor].get(mes, 0)
                linha.append(round(valor, 2))
            dados_matriz.append(linha)
        
        # Formata labels dos meses
        meses_labels = []
        for mes in meses_ordenados:
            try:
                mes_date = datetime.strptime(mes + '-01', '%Y-%m-%d')
                nomes_meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
                ano = mes_date.strftime('%y')
                mes_nome = nomes_meses[mes_date.month - 1]
                meses_labels.append(f"{mes_nome}/{ano}")
            except:
                meses_labels.append(mes)
        
        return {
            'setores': setores,
            'meses': meses_labels,
            'dados': dados_matriz,  # Lista de listas: [setor][mes]
            'total_setores': len(setores),
            'total_meses': len(meses_ordenados)
        }
    
    def top_cids_por_setor(self, client_id: int, top_n: int = 3, mes_inicio: str = None, mes_fim: str = None, funcionario: str = None) -> List[Dict[str, Any]]:
        """
        Retorna os top CIDs de cada setor
        Útil para identificar problemas específicos por área
        """
        # Busca todos os setores
        query_setores = self.db.query(
            Atestado.setor
        ).join(Upload).filter(
            Upload.client_id == client_id
        ).distinct()
        
        if mes_inicio:
            query_setores = query_setores.filter(Upload.mes_referencia >= mes_inicio)
        if mes_fim:
            query_setores = query_setores.filter(Upload.mes_referencia <= mes_fim)
        
        setores = [r.setor for r in query_setores.all() if r.setor]
        
        resultado = []
        
        for setor in setores:
            # Busca top CIDs deste setor
            query = self.db.query(
                Atestado.cid,
                Atestado.doenca,
                func.sum(Atestado.dias_atestados).label('total_dias'),
                func.count(Atestado.id).label('quantidade')
            ).join(Upload).filter(
                Upload.client_id == client_id,
                Atestado.setor == setor
            ).group_by(
                Atestado.cid,
                Atestado.doenca
            ).order_by(
                func.sum(Atestado.dias_atestados).desc()
            ).limit(top_n)
            
            if mes_inicio:
                query = query.filter(Upload.mes_referencia >= mes_inicio)
            if mes_fim:
                query = query.filter(Upload.mes_referencia <= mes_fim)
            
            from .analytics_helper import aplicar_filtro_funcionario
            query = aplicar_filtro_funcionario(query, funcionario)
            
            cids = query.all()
            
            cids_lista = []
            for c in cids:
                cids_lista.append({
                    'cid': c.cid or 'N/A',
                    'doenca': c.doenca or 'Não informado',
                    'dias_perdidos': round(float(c.total_dias or 0), 2),
                    'quantidade': c.quantidade or 0
                })
            
            if cids_lista:  # Só adiciona se houver dados
                resultado.append({
                    'setor': setor,
                    'top_cids': cids_lista
                })
        
        return resultado