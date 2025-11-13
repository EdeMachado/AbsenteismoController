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
    
    def _verificar_campo_disponivel(self, client_id: int, campo: str) -> bool:
        """Verifica se um campo tem dados disponíveis para o cliente"""
        try:
            amostra = self.db.query(Atestado).join(Upload).filter(
                Upload.client_id == client_id
            ).limit(100).all()
            
            if not amostra:
                return False
            
            return any(
                getattr(reg, campo, None) not in (None, '', 0, 0.0) 
                for reg in amostra
            )
        except:
            return False
    
    def gerar_insights(self, client_id: int) -> List[Dict[str, Any]]:
        """Gera insights automáticos baseados nos campos disponíveis"""
        insights = []
        
        # 1. TOP CID mais frequente (só se tiver campo CID)
        if self._verificar_campo_disponivel(client_id, 'cid') or self._verificar_campo_disponivel(client_id, 'diagnostico'):
            try:
                top_cid = self.db.query(
                    Atestado.cid,
                    Atestado.diagnostico,
                    func.count(Atestado.id).label('qtd')
                ).join(Upload).filter(
                    Upload.client_id == client_id,
                    Atestado.cid != '',
                    Atestado.cid.isnot(None)
                ).group_by(Atestado.cid, Atestado.diagnostico).order_by(func.count(Atestado.id).desc()).first()
                
                if top_cid and top_cid.qtd > 0:
                    insights.append({
                        'tipo': 'alerta',
                        'icone': '🩺',
                        'titulo': f'CID {top_cid.cid} - Mais Frequente',
                        'descricao': f'{top_cid.diagnostico or "Doença não especificada"} aparece em {top_cid.qtd} atestados ({self._percentual(top_cid.qtd, client_id)}% do total)',
                        'recomendacao': self._get_recomendacao_cid(top_cid.cid)
                    })
            except Exception as e:
                print(f"Erro ao gerar insight de CID: {e}")
        
        # 2. Setor com mais atestados (só se tiver campo setor)
        if self._verificar_campo_disponivel(client_id, 'setor'):
            try:
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
            except Exception as e:
                print(f"Erro ao gerar insight de setor: {e}")
        
        # 3. Análise de gênero (só se tiver campo genero)
        if self._verificar_campo_disponivel(client_id, 'genero'):
            try:
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
            except Exception as e:
                print(f"Erro ao gerar insight de gênero: {e}")
        
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
            func.sum(Atestado.dias_atestados)
        ).join(Upload).filter(
            Upload.client_id == client_id,
            (Atestado.dias_atestados > 0) | (Atestado.dias_perdidos > 0)
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
    
    def gerar_analise_grafico(self, tipo_grafico: str, dados: Any, metricas: Dict[str, Any] = None) -> str:
        """Gera análise textual específica para cada tipo de gráfico"""
        
        if tipo_grafico == 'kpis':
            total_dias = metricas.get('total_dias_perdidos', 0) if metricas else 0
            total_horas = metricas.get('total_horas_perdidas', 0) if metricas else 0
            total_atestados = metricas.get('total_atestados_dias', 0) if metricas else 0
            
            analise = f"""📊 **Visão Geral dos Indicadores**

O período analisado apresenta **{int(total_dias)} dias perdidos** e **{int(total_horas)} horas perdidas**, distribuídos em **{int(total_atestados)} atestados**.

Estes números representam o impacto direto do absenteísmo na operação, impactando a produtividade e exigindo atenção para ações preventivas e de gestão de saúde ocupacional.

💡 **Recomendação**: Implementar programa de gestão de absenteísmo com foco em prevenção e acompanhamento individualizado."""
            
        elif tipo_grafico == 'funcionarios_dias':
            if not dados or len(dados) == 0:
                return "Não há dados suficientes para análise."
            
            top = dados[0]
            top5_total = sum(d.get('dias_perdidos', 0) for d in dados[:5])
            total_dias = metricas.get('total_dias_perdidos', 0) if metricas else top5_total
            pct_top5 = (top5_total / total_dias * 100) if total_dias > 0 else 0
            
            analise = f"""👤 **Análise: Dias Perdidos por Funcionário**

O funcionário **{top.get('nome', 'N/A')}** apresenta **{int(top.get('dias_perdidos', 0))} dias perdidos**, representando o maior índice individual de afastamento.

Os **5 funcionários com maior incidência** concentram **{pct_top5:.1f}%** do total de dias perdidos, indicando necessidade de foco em ações preventivas específicas para este grupo.

💡 **Recomendação**: Implementar programa de acompanhamento individualizado para funcionários com alto índice de absenteísmo, incluindo avaliação de saúde ocupacional e apoio multidisciplinar."""
            
        elif tipo_grafico == 'top_cids':
            if not dados or len(dados) == 0:
                return "Não há dados suficientes para análise."
            
            top = dados[0]
            total_cids = sum(d.get('quantidade', 0) for d in dados)
            pct_top = (top.get('quantidade', 0) / total_cids * 100) if total_cids > 0 else 0
            
            analise = f"""🩺 **Análise: TOP 10 Doenças mais Frequentes**

O **CID {top.get('cid', 'N/A')}** - **{top.get('diagnostico', 'Diagnóstico não especificado')}** é a principal causa de afastamento, com **{top.get('quantidade', 0)} ocorrências**, representando **{pct_top:.1f}%** do total.

As doenças mais frequentes indicam padrões que podem estar relacionados a condições de trabalho, fatores ambientais ou questões de saúde populacional específicas da organização.

💡 **Recomendação**: Implementar ações preventivas específicas para as principais causas identificadas, incluindo programas de saúde ocupacional, ergonomia e qualidade de vida no trabalho."""
            
        elif tipo_grafico == 'evolucao_mensal':
            if not dados or len(dados) < 2:
                return "Não há dados suficientes para análise de tendência."
            
            ultimo = dados[-1]
            penultimo = dados[-2]
            variacao = ((ultimo.get('dias_perdidos', 0) - penultimo.get('dias_perdidos', 0)) / penultimo.get('dias_perdidos', 1) * 100) if penultimo.get('dias_perdidos', 0) > 0 else 0
            
            analise = f"""📈 **Análise: Evolução Mensal - Últimos 12 Meses**

A análise da tendência mostra uma **{"variação positiva" if variacao > 0 else "variação negativa"} de {abs(variacao):.1f}%** comparando o último mês ({ultimo.get('mes', 'N/A')}) com o anterior ({penultimo.get('mes', 'N/A')}).

Esta evolução indica a necessidade de monitoramento contínuo e ajuste das estratégias de gestão de absenteísmo conforme a tendência observada.

💡 **Recomendação**: {"Manter atenção às ações preventivas e investigar causas do aumento" if variacao > 0 else "Manter as ações atuais e buscar consolidar a redução observada"}."""
            
        elif tipo_grafico == 'top_setores':
            if not dados or len(dados) == 0:
                return "Não há dados suficientes para análise."
            
            top = dados[0]
            total_setores = sum(d.get('quantidade', 0) for d in dados)
            pct_top = (top.get('quantidade', 0) / total_setores * 100) if total_setores > 0 else 0
            
            analise = f"""🏢 **Análise: TOP 5 Setores**

O setor **{top.get('setor', 'N/A')}** apresenta o maior índice de atestados, com **{top.get('quantidade', 0)} ocorrências**, representando **{pct_top:.1f}%** do total.

Esta concentração pode indicar questões específicas relacionadas a condições de trabalho, carga horária, ergonomia ou fatores organizacionais deste setor.

💡 **Recomendação**: Realizar avaliação detalhada das condições de trabalho no setor, incluindo análise ergonômica, gestão de carga de trabalho e programa de saúde ocupacional específico."""
            
        elif tipo_grafico == 'genero':
            if not dados or len(dados) < 2:
                return "Não há dados suficientes para análise."
            
            total = sum(d.get('quantidade', 0) for d in dados)
            maior = max(dados, key=lambda x: x.get('quantidade', 0))
            pct = (maior.get('quantidade', 0) / total * 100) if total > 0 else 0
            
            genero_nome = "Masculino" if maior.get('genero') == 'M' else "Feminino"
            
            analise = f"""👥 **Análise: Distribuição por Gênero**

Funcionários do sexo **{genero_nome}** representam **{pct:.1f}%** dos atestados ({maior.get('quantidade', 0)} de {total} total).

Esta distribuição pode refletir características demográficas da organização ou indicar necessidades específicas de atenção à saúde de acordo com o perfil de gênero.

💡 **Recomendação**: Considerar ações de saúde preventiva específicas por gênero, respeitando as particularidades e necessidades de cada grupo."""
            
        elif tipo_grafico == 'dias_doenca':
            if not dados or len(dados) == 0:
                return "Não há dados suficientes para análise."
            
            top = dados[0]
            total_dias = sum(d.get('dias_perdidos', 0) for d in dados)
            pct = (top.get('dias_perdidos', 0) / total_dias * 100) if total_dias > 0 else 0
            
            analise = f"""📊 **Análise: Dias por Doença**

O diagnóstico **{top.get('descricao', top.get('cid', 'N/A'))}** apresenta **{int(top.get('dias_perdidos', 0))} dias perdidos**, representando **{pct:.1f}%** do total.

Esta análise permite identificar as condições de saúde que geram maior impacto em termos de tempo de afastamento, orientando ações preventivas e de gestão de saúde.

💡 **Recomendação**: Desenvolver programa de prevenção específico para as principais causas de afastamento de maior duração."""
            
        elif tipo_grafico == 'escalas':
            if not dados or len(dados) == 0:
                return "Não há dados suficientes para análise."
            
            top = dados[0]
            total = sum(d.get('quantidade', 0) for d in dados)
            pct = (top.get('quantidade', 0) / total * 100) if total > 0 else 0
            
            analise = f"""⏰ **Análise: Escalas com mais Atestados**

A escala **{top.get('escala', 'N/A')}** apresenta o maior número de atestados, com **{top.get('quantidade', 0)} ocorrências ({pct:.1f}% do total)**.

Esta informação pode indicar relação entre horários de trabalho e incidência de afastamentos, possivelmente relacionada a fatores como fadiga, privação de sono ou condições específicas de cada turno.

💡 **Recomendação**: Avaliar condições de trabalho específicas das escalas com maior incidência, considerando ajustes de carga horária, pausas e programas de saúde para trabalhadores em turnos."""
            
        elif tipo_grafico == 'motivos':
            if not dados or len(dados) == 0:
                return "Não há dados suficientes para análise."
            
            top = dados[0]
            total = sum(d.get('quantidade', 0) for d in dados)
            pct = (top.get('quantidade', 0) / total * 100) if total > 0 else 0
            
            analise = f"""📋 **Análise: Motivos de Incidência**

O motivo **{top.get('motivo', 'N/A')}** é o principal responsável pelos atestados, com **{pct:.1f}%** das ocorrências ({top.get('quantidade', 0)} de {total} total).

Esta distribuição permite identificar padrões nas causas de afastamento, orientando estratégias de prevenção e gestão de saúde ocupacional.

💡 **Recomendação**: Desenvolver ações preventivas específicas para os principais motivos identificados, com foco em redução de incidência e promoção de saúde."""
            
        elif tipo_grafico == 'centro_custo':
            if not dados or len(dados) == 0:
                return "Não há dados suficientes para análise."
            
            top = dados[0]
            total_dias = sum(d.get('dias_perdidos', 0) for d in dados)
            pct = (top.get('dias_perdidos', 0) / total_dias * 100) if total_dias > 0 else 0
            
            analise = f"""💰 **Análise: Dias Perdidos por Centro de Custo (Setor)**

O setor **{top.get('setor', 'N/A')}** apresenta o maior impacto em dias perdidos, com **{int(top.get('dias_perdidos', 0))} dias ({pct:.1f}% do total)**.

Esta análise permite identificar os setores que demandam maior atenção em termos de gestão de absenteísmo e saúde ocupacional.

💡 **Recomendação**: Implementar programa de gestão de saúde ocupacional específico para os setores com maior impacto, incluindo avaliações periódicas e ações preventivas."""
            
        elif tipo_grafico == 'distribuicao_dias':
            if not dados or len(dados) == 0:
                return "Não há dados suficientes para análise."
            
            # Encontra a faixa mais comum
            mais_comum = max(dados, key=lambda x: x.get('quantidade', 0))
            media = sum(d.get('dias', 0) * d.get('quantidade', 0) for d in dados) / sum(d.get('quantidade', 0) for d in dados) if sum(d.get('quantidade', 0) for d in dados) > 0 else 0
            
            analise = f"""📊 **Análise: Distribuição de Dias por Atestado**

A maioria dos atestados concentra-se na faixa de **{mais_comum.get('dias', 'N/A')} dias**, com média geral de **{media:.1f} dias por atestado**.

Esta distribuição permite entender o padrão de duração dos afastamentos, orientando estratégias de gestão e acompanhamento.

💡 **Recomendação**: Estabelecer protocolos de acompanhamento diferenciados conforme a duração esperada do afastamento, priorizando casos de maior duração."""
            
        elif tipo_grafico == 'media_cid':
            if not dados or len(dados) == 0:
                return "Não há dados suficientes para análise."
            
            top = dados[0]
            
            analise = f"""📊 **Análise: Média de Dias por CID**

O **CID {top.get('cid', 'N/A')}** apresenta a maior média de dias por ocorrência, com **{top.get('media_dias', 0):.1f} dias** em média.

Esta informação permite identificar as condições de saúde que demandam maior tempo de recuperação, orientando estratégias de prevenção e gestão.

💡 **Recomendação**: Desenvolver programa de prevenção específico para as condições com maior média de dias, incluindo ações de promoção de saúde e acompanhamento."""
            
        elif tipo_grafico == 'setor_genero':
            if not dados or len(dados) == 0:
                return "Não há dados suficientes para análise."
            
            # Encontra setor com maior diferença
            maior_diferenca = 0
            setor_analise = None
            for item in dados:
                masculino = item.get('masculino', 0)
                feminino = item.get('feminino', 0)
                diferenca = abs(masculino - feminino)
                if diferenca > maior_diferenca:
                    maior_diferenca = diferenca
                    setor_analise = item
            
            if setor_analise:
                analise = f"""👥 **Análise: Dias Perdidos por Setor e Gênero**

O setor **{setor_analise.get('setor', 'N/A')}** apresenta diferença significativa entre gêneros: **{int(setor_analise.get('masculino', 0))} dias (M)** vs **{int(setor_analise.get('feminino', 0))} dias (F)**.

Esta análise permite identificar padrões específicos por setor e gênero, orientando ações preventivas direcionadas.

💡 **Recomendação**: Investigar causas específicas da diferença observada e desenvolver ações preventivas considerando as particularidades de cada grupo."""
            else:
                analise = "Não foi possível identificar padrões significativos na distribuição por setor e gênero."
            
        else:
            analise = "Análise não disponível para este tipo de gráfico."
        
        return analise


