"""
Insights - Geração automática de análises e recomendações
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
from .models import Atestado, Upload
import json

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
            
            tem_campo = any(
                getattr(reg, campo, None) not in (None, '', 0, 0.0) 
                for reg in amostra
            )
            return tem_campo
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False
    
    def _verificar_coluna_original(self, client_id: int, nomes_colunas: List[str]) -> bool:
        """Verifica se há uma coluna específica nos dados originais da planilha"""
        try:
            import json
            amostra = self.db.query(Atestado.dados_originais).join(Upload).filter(
                Upload.client_id == client_id,
                Atestado.dados_originais.isnot(None)
            ).limit(10).all()
            
            if not amostra:
                return False
            
            # Verifica se alguma das colunas existe nos dados originais
            for row in amostra:
                if row[0]:
                    try:
                        dados = json.loads(row[0])
                        # Verifica se alguma das colunas procuradas existe (case-insensitive)
                        for col_original in dados.keys():
                            col_upper = col_original.upper()
                            for nome_procurado in nomes_colunas:
                                if nome_procurado.upper() in col_upper or col_upper in nome_procurado.upper():
                                    print(f"[INSIGHTS] Coluna de gênero encontrada nos dados originais: '{col_original}'")
                                    return True
                    except:
                        continue
            
            return False
        except Exception as e:
            print(f"[INSIGHTS] Erro ao verificar coluna original: {e}")
            return False
    
    def gerar_insights(self, client_id: int) -> List[Dict[str, Any]]:
        """Gera insights automáticos baseados nos campos disponíveis"""
        insights = []
        
        # 1. Doença mais frequente - USA OS MESMOS DADOS DO GRÁFICO
        # Para Roda de Ouro: usa classificacao_doencas_roda_ouro (por nome da doença)
        # Para outros: usa top_cids (por CID)
        try:
            from .analytics import Analytics
            analytics = Analytics(self.db)
            
            # RODA DE OURO: usa classificação por doença (mesma do gráfico)
            if client_id == 4:
                doencas_list = analytics.classificacao_doencas_roda_ouro(client_id, limit=1)
                
                if doencas_list and len(doencas_list) > 0:
                    top_doenca_data = doencas_list[0]  # Primeiro item (mais dias)
                    nome_doenca = top_doenca_data.get('tipo_doenca', 'Não informado')
                    dias_doenca = top_doenca_data.get('quantidade', 0)
                    
                    
                    # Calcula total de dias para percentual
                    total_dias = self.db.query(
                        func.sum(Atestado.dias_atestados)
                    ).join(Upload).filter(
                        Upload.client_id == client_id,
                        Atestado.dias_atestados > 0
                    ).scalar() or 0
                    
                    pct_dias = (dias_doenca / total_dias * 100) if total_dias > 0 else 0
                    
                    insights.append({
                        'tipo': 'alerta',
                        'icone': '🩺',
                        'titulo': f'Doença com Maior Impacto',
                        'descricao': f'{nome_doenca} apresenta {int(dias_doenca)} dias de afastamento ({pct_dias:.1f}% do total de dias perdidos)',
                        'recomendacao': 'Desenvolver programa de prevenção específico para esta condição, incluindo ações educativas e acompanhamento médico especializado'
                    })
            else:
                # OUTROS CLIENTES: usa top_cids (por CID)
                top_cids_list = analytics.top_cids(client_id, limit=1)
                
                if top_cids_list and len(top_cids_list) > 0:
                    top_cid_data = top_cids_list[0]
                    cid = top_cid_data.get('cid')
                    diagnostico = top_cid_data.get('descricao', '')
                    quantidade = top_cid_data.get('quantidade', 0)
                    dias_perdidos = top_cid_data.get('dias_perdidos', 0)
                    
                    diagnostico_texto = diagnostico
                    if not diagnostico_texto or diagnostico_texto.strip() == '' or diagnostico_texto == 'Não informado':
                        diagnostico_texto = self._get_descricao_cid(cid)
                    
                    dias_perdidos_texto = f" e {int(dias_perdidos)} dias de afastamento" if dias_perdidos and dias_perdidos > 0 else ""
                    
                    insights.append({
                        'tipo': 'alerta',
                        'icone': '🩺',
                        'titulo': f'CID {cid} - Mais Frequente',
                        'descricao': f'{diagnostico_texto} aparece em {quantidade} atestados ({self._percentual(quantidade, client_id)}% do total){dias_perdidos_texto}',
                        'recomendacao': self._get_recomendacao_cid(cid)
                    })
        except Exception as e:
            print(f"Erro ao gerar insight de doença/CID: {e}")
            import traceback
            traceback.print_exc()
        
        # 2. Setor com mais atestados (usa a mesma lógica do gráfico para garantir consistência)
        if self._verificar_campo_disponivel(client_id, 'setor'):
            try:
                # USA A MESMA FUNÇÃO DO GRÁFICO para garantir que o insight sempre bata com o gráfico
                from .analytics import Analytics
                analytics = Analytics(self.db)
                top_setores_list = analytics.top_setores(client_id, limit=1)  # Pega apenas o primeiro (mais frequente)
                
                if top_setores_list and len(top_setores_list) > 0:
                    top_setor_data = top_setores_list[0]  # Primeiro item da lista (mais frequente)
                    setor = top_setor_data.get('setor')
                    quantidade = top_setor_data.get('quantidade', 0)
                    dias_perdidos = top_setor_data.get('dias_perdidos', 0)
                    
                    dias_texto = f" e {int(dias_perdidos)} dias de afastamento" if dias_perdidos and dias_perdidos > 0 else ""
                    
                    insights.append({
                        'tipo': 'atencao',
                        'icone': '🏢',
                        'titulo': f'Setor {setor} - Maior Índice',
                        'descricao': f'{quantidade} atestados registrados ({self._percentual(quantidade, client_id)}% do total){dias_texto}',
                        'recomendacao': 'Avaliar condições de trabalho e ergonomia neste setor'
                    })
            except Exception as e:
                print(f"Erro ao gerar insight de setor: {e}")
        
        # 3. Análise de gênero (só se tiver campo genero E se vier da planilha, não detectado automaticamente)
        # Verifica se há coluna de gênero nos dados originais (não apenas detecção automática)
        if self._verificar_campo_disponivel(client_id, 'genero'):
            try:
                # Verifica se há coluna de gênero nos dados originais
                tem_coluna_genero = self._verificar_coluna_original(client_id, ['genero', 'gênero', 'sexo', 'gender'])
                
                if not tem_coluna_genero:
                    # Se não tem coluna de gênero na planilha, não mostra insight (é detecção automática)
                    print(f"[INSIGHTS] Gênero detectado automaticamente, mas não há coluna na planilha. Pulando insight de gênero.")
                else:
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
        
        # 5. Funcionário com mais atestados (usa a mesma lógica do gráfico para garantir consistência)
        if self._verificar_campo_disponivel(client_id, 'nomecompleto') or self._verificar_campo_disponivel(client_id, 'nome_funcionario'):
            try:
                # USA A MESMA FUNÇÃO DO GRÁFICO para garantir que o insight sempre bata com o gráfico
                from .analytics import Analytics
                analytics = Analytics(self.db)
                top_funcionarios_list = analytics.top_funcionarios(client_id, limit=1)  # Pega apenas o primeiro (mais frequente)
                
                if top_funcionarios_list and len(top_funcionarios_list) > 0:
                    top_funcionario_data = top_funcionarios_list[0]  # Primeiro item da lista (mais frequente)
                    nome = top_funcionario_data.get('nome', 'N/A')
                    quantidade = top_funcionario_data.get('quantidade', 0)
                    dias_perdidos = top_funcionario_data.get('dias_perdidos', 0)
                    
                    dias_texto = f" e {int(dias_perdidos)} dias de afastamento" if dias_perdidos and dias_perdidos > 0 else ""
                    
                    insights.append({
                        'tipo': 'atencao',
                        'icone': '👤',
                        'titulo': f'Funcionário com Mais Atestados',
                        'descricao': f'{nome} registrou {quantidade} atestados ({self._percentual(quantidade, client_id)}% do total){dias_texto}',
                        'recomendacao': 'Acompanhar individualmente este funcionário e avaliar necessidade de apoio médico ou psicológico'
                    })
            except Exception as e:
                print(f"Erro ao gerar insight de funcionário: {e}")
        
        # 6. Dias perdidos alto
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
        
        # 7. Análise de Tempo de Serviço (especialmente para RODA DE OURO)
        if client_id == 4:  # RODA DE OURO
            try:
                from .analytics import Analytics
                analytics = Analytics(self.db)
                tempo_servico = analytics.tempo_servico_atestados(client_id)
                
                if tempo_servico and len(tempo_servico) > 0:
                    # Encontra a faixa com mais dias
                    faixa_mais_dias = max(tempo_servico, key=lambda x: x.get('dias_afastamento', 0))
                    total_dias_tempo = sum(t.get('dias_afastamento', 0) for t in tempo_servico)
                    pct = (faixa_mais_dias.get('dias_afastamento', 0) / total_dias_tempo * 100) if total_dias_tempo > 0 else 0
                    
                    if pct > 30:  # Se uma faixa concentra mais de 30% dos dias
                        insights.append({
                            'tipo': 'info',
                            'icone': '⏱️',
                            'titulo': f'Funcionários com {faixa_mais_dias.get("faixa_tempo_servico", "N/A")} - Maior Incidência',
                            'descricao': f'{pct:.1f}% dos dias de afastamento ({int(faixa_mais_dias.get("dias_afastamento", 0))} dias) concentram-se em funcionários com {faixa_mais_dias.get("faixa_tempo_servico", "N/A")} de empresa',
                            'recomendacao': 'Avaliar se funcionários mais antigos ou mais novos precisam de atenção especial em programas de saúde ocupacional'
                        })
            except Exception as e:
                print(f"Erro ao gerar insight de tempo de serviço: {e}")
        
        return insights
    
    def _percentual(self, valor: int, client_id: int) -> float:
        """Calcula percentual em relação ao total"""
        total = self.db.query(func.count(Atestado.id)).join(Upload).filter(
            Upload.client_id == client_id
        ).scalar() or 1
        
        return round((valor / total * 100), 1)
    
    def _get_descricao_cid(self, cid: str) -> str:
        """Retorna descrição mais específica baseada no CID"""
        descricoes = {
            'A09': 'Gastroenterite e colite de origem infecciosa',
            'J11': 'Influenza (gripe)',
            'J06': 'Infecções agudas das vias aéreas superiores',
            'J069': 'Infecção aguda das vias aéreas superiores não especificada',
            'M54': 'Dorsalgia (dor nas costas)',
            'M54.5': 'Cervicalgia (dor no pescoço)',
            'M79': 'Outros transtornos dos tecidos moles',
            'M796': 'Dor em membro',
            'M650': 'Tenossinovite estenosante',
            'R51': 'Cefaleia (dor de cabeça)',
            'Z00': 'Exame médico geral',
            'Z00.8': 'Outros exames médicos gerais',
        }
        
        # Tenta primeiro o CID completo, depois os primeiros 3 caracteres
        if cid in descricoes:
            return descricoes[cid]
        
        cid_grupo = cid[:3] if cid else ''
        if cid_grupo in descricoes:
            return descricoes[cid_grupo]
        
        return f'Doença relacionada ao CID {cid}'
    
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
            'J11': 'Reforçar medidas de prevenção de gripe e vacinação',
            'J06': 'Melhorar higiene e ventilação dos ambientes',
        }
        
        # Pega primeiros 3 caracteres do CID
        cid_grupo = cid[:3] if cid else ''
        
        return recomendacoes.get(cid_grupo, 'Investigar causas e implementar ações preventivas')
    
    def gerar_analise_grafico(self, tipo_grafico: str, dados: Any, metricas: Dict[str, Any] = None) -> str:
        """Gera análise textual específica para cada tipo de gráfico"""
        
        if tipo_grafico == 'kpis':
            total_dias = metricas.get('total_dias_perdidos', 0) if metricas else 0
            total_horas = metricas.get('total_horas_perdidas', 0) if metricas else 0
            # CORREÇÃO: usa total_atestados (quantidade de registros), não total_atestados_dias (soma de dias)
            total_atestados = metricas.get('total_atestados', 0) if metricas else 0
            
            analise = f"""📊 **Visão Geral dos Indicadores**

O período analisado apresenta **{int(total_dias)} dias perdidos** e **{int(total_horas)} horas perdidas**, distribuídos em **{int(total_atestados)} atestados**.

Estes números representam o impacto direto do absenteísmo na operação, impactando a produtividade e exigindo atenção para ações preventivas e de gestão de saúde ocupacional.

💡 **Recomendação**: Implementar programa de gestão de absenteísmo com foco em prevenção e acompanhamento individualizado."""
            
        elif tipo_grafico == 'funcionarios_dias':
            # Validação mais flexível: aceita dados mesmo se vazio, desde que tenha estrutura
            if not dados:
                return "📊 **Análise: Dias Perdidos por Funcionário**\n\nDados ainda não disponíveis para este período."
            
            # Se for lista vazia, tenta usar métricas
            if isinstance(dados, list) and len(dados) == 0:
                total_dias = metricas.get('total_dias_perdidos', 0) if metricas else 0
                if total_dias > 0:
                    analise = f"""📊 **Análise: Dias Perdidos por Funcionário**

O período analisado apresenta **{int(total_dias)} dias perdidos** distribuídos entre os funcionários.

💡 **Recomendação**: Implementar programa de acompanhamento individualizado para funcionários com alto índice de absenteísmo."""
                    return analise
                return "📊 **Análise: Dias Perdidos por Funcionário**\n\nDados ainda não disponíveis para este período."
            
            top = dados[0] if isinstance(dados, list) else dados
            top5_total = sum(d.get('dias_perdidos', 0) for d in (dados[:5] if isinstance(dados, list) else [dados]))
            total_dias = metricas.get('total_dias_perdidos', 0) if metricas else top5_total
            pct_top5 = (top5_total / total_dias * 100) if total_dias > 0 else 0
            
            nome_funcionario = top.get('nome', 'Não informado') if isinstance(top, dict) else 'Não informado'
            if nome_funcionario == 'N/A' or not nome_funcionario:
                nome_funcionario = 'Não informado'
            
            dias_perdidos = int(top.get('dias_perdidos', 0)) if isinstance(top, dict) else 0
            
            analise = f"""👤 **Análise: Dias Perdidos por Funcionário**

O funcionário **{nome_funcionario}** apresenta **{dias_perdidos} dias perdidos**, representando o maior índice individual de afastamento.

Os **5 funcionários com maior incidência** concentram **{pct_top5:.1f}%** do total de dias perdidos, indicando necessidade de foco em ações preventivas específicas para este grupo.

💡 **Recomendação**: Implementar programa de acompanhamento individualizado para funcionários com alto índice de absenteísmo, incluindo avaliação de saúde ocupacional e apoio multidisciplinar."""
            
        elif tipo_grafico == 'top_cids':
            if not dados:
                return "📊 **Análise: TOP 10 Doenças mais Frequentes**\n\nDados ainda não disponíveis para este período."
            
            if isinstance(dados, list) and len(dados) == 0:
                return "📊 **Análise: TOP 10 Doenças mais Frequentes**\n\nDados ainda não disponíveis para este período."
            
            top = dados[0]
            total_cids = sum(d.get('quantidade', 0) for d in dados)
            pct_top = (top.get('quantidade', 0) / total_cids * 100) if total_cids > 0 else 0
            
            # CORREÇÃO: Se descricao = cid (sem diagnóstico), mostra apenas o código
            cid_codigo = top.get('cid', 'Não informado')
            if cid_codigo == 'N/A' or not cid_codigo:
                cid_codigo = 'Não informado'
            
            cid_descricao = top.get('descricao', top.get('diagnostico', ''))
            if not cid_descricao or cid_descricao == 'N/A' or cid_descricao == cid_codigo:
                texto_cid = f"**CID {cid_codigo}**"
            else:
                texto_cid = f"**CID {cid_codigo}** - **{cid_descricao}**"
            
            analise = f"""🩺 **Análise: TOP 10 Doenças mais Frequentes**

O {texto_cid} é a principal causa de afastamento, com **{top.get('quantidade', 0)} ocorrências**, representando **{pct_top:.1f}%** do total.

As doenças mais frequentes indicam padrões que podem estar relacionados a condições de trabalho, fatores ambientais ou questões de saúde populacional específicas da organização.

💡 **Recomendação**: Implementar ações preventivas específicas para as principais causas identificadas, incluindo programas de saúde ocupacional, ergonomia e qualidade de vida no trabalho."""
            
        elif tipo_grafico == 'evolucao_mensal':
            if not dados:
                return "📈 **Análise: Evolução Mensal**\n\nDados ainda não disponíveis para este período."
            
            if isinstance(dados, list) and len(dados) < 2:
                if len(dados) == 1:
                    item = dados[0]
                    dias = item.get('dias_perdidos', 0) if isinstance(item, dict) else 0
                    mes = item.get('mes', 'Período') if isinstance(item, dict) else 'Período'
                    analise = f"""📈 **Análise: Evolução Mensal**

O período analisado ({mes}) apresenta **{int(dias)} dias perdidos**.

💡 **Recomendação**: Continuar monitorando a evolução mensal para identificar tendências."""
                    return analise
                return "📈 **Análise: Evolução Mensal**\n\nDados ainda não disponíveis para este período."
            
            ultimo = dados[-1]
            penultimo = dados[-2]
            variacao = ((ultimo.get('dias_perdidos', 0) - penultimo.get('dias_perdidos', 0)) / penultimo.get('dias_perdidos', 1) * 100) if penultimo.get('dias_perdidos', 0) > 0 else 0
            
            mes_ultimo = ultimo.get('mes', 'Último mês')
            mes_penultimo = penultimo.get('mes', 'Mês anterior')
            if mes_ultimo == 'N/A' or not mes_ultimo:
                mes_ultimo = 'Último mês'
            if mes_penultimo == 'N/A' or not mes_penultimo:
                mes_penultimo = 'Mês anterior'
            
            analise = f"""📈 **Análise: Evolução Mensal - Últimos 12 Meses**

A análise da tendência mostra uma **{"variação positiva" if variacao > 0 else "variação negativa"} de {abs(variacao):.1f}%** comparando o último mês ({mes_ultimo}) com o anterior ({mes_penultimo}).

Esta evolução indica a necessidade de monitoramento contínuo e ajuste das estratégias de gestão de absenteísmo conforme a tendência observada.

💡 **Recomendação**: {"Manter atenção às ações preventivas e investigar causas do aumento" if variacao > 0 else "Manter as ações atuais e buscar consolidar a redução observada"}."""
            
        elif tipo_grafico == 'top_setores':
            if not dados:
                return "🏢 **Análise: TOP 5 Setores**\n\nDados ainda não disponíveis para este período."
            
            if isinstance(dados, list) and len(dados) == 0:
                return "🏢 **Análise: TOP 5 Setores**\n\nDados ainda não disponíveis para este período."
            
            top = dados[0]
            total_setores = sum(d.get('quantidade', 0) for d in dados)
            pct_top = (top.get('quantidade', 0) / total_setores * 100) if total_setores > 0 else 0
            
            setor_nome = top.get('setor', 'Não informado')
            if setor_nome == 'N/A' or not setor_nome:
                setor_nome = 'Não informado'
            
            analise = f"""🏢 **Análise: TOP 5 Setores**

O setor **{setor_nome}** apresenta o maior índice de atestados, com **{top.get('quantidade', 0)} ocorrências**, representando **{pct_top:.1f}%** do total.

Esta concentração pode indicar questões específicas relacionadas a condições de trabalho, carga horária, ergonomia ou fatores organizacionais deste setor.

💡 **Recomendação**: Realizar avaliação detalhada das condições de trabalho no setor, incluindo análise ergonômica, gestão de carga de trabalho e programa de saúde ocupacional específico."""
            
        elif tipo_grafico == 'genero':
            if not dados:
                return "👥 **Análise: Distribuição por Gênero**\n\nDados ainda não disponíveis para este período."
            
            if isinstance(dados, list) and len(dados) < 2:
                if len(dados) == 1:
                    item = dados[0]
                    genero_nome = "Masculino" if item.get('genero') == 'M' else "Feminino" if item.get('genero') == 'F' else "Não informado"
                    quantidade = item.get('quantidade', 0) if isinstance(item, dict) else 0
                    analise = f"""👥 **Análise: Distribuição por Gênero**

Funcionários do sexo **{genero_nome}** representam **{quantidade} atestados** no período analisado.

💡 **Recomendação**: Considerar ações de saúde preventiva específicas por gênero."""
                    return analise
                return "👥 **Análise: Distribuição por Gênero**\n\nDados ainda não disponíveis para este período."
            
            total = sum(d.get('quantidade', 0) for d in dados)
            maior = max(dados, key=lambda x: x.get('quantidade', 0))
            pct = (maior.get('quantidade', 0) / total * 100) if total > 0 else 0
            
            genero_nome = "Masculino" if maior.get('genero') == 'M' else "Feminino"
            
            analise = f"""👥 **Análise: Distribuição por Gênero**

Funcionários do sexo **{genero_nome}** representam **{pct:.1f}%** dos atestados ({maior.get('quantidade', 0)} de {total} total).

Esta distribuição pode refletir características demográficas da organização ou indicar necessidades específicas de atenção à saúde de acordo com o perfil de gênero.

💡 **Recomendação**: Considerar ações de saúde preventiva específicas por gênero, respeitando as particularidades e necessidades de cada grupo."""
            
        elif tipo_grafico == 'dias_doenca':
            if not dados:
                return "📊 **Análise: Dias por Doença**\n\nDados ainda não disponíveis para este período."
            
            if isinstance(dados, list) and len(dados) == 0:
                return "📊 **Análise: Dias por Doença**\n\nDados ainda não disponíveis para este período."
            
            top = dados[0]
            total_dias = sum(d.get('dias_perdidos', 0) for d in dados)
            pct = (top.get('dias_perdidos', 0) / total_dias * 100) if total_dias > 0 else 0
            
            # CORREÇÃO: Se descricao = cid (sem diagnóstico), mostra apenas o código
            cid_codigo = top.get('cid', 'N/A')
            cid_descricao = top.get('descricao', top.get('diagnostico', cid_codigo))
            
            if cid_descricao == cid_codigo:
                texto_cid = f"**CID {cid_codigo}**"
            else:
                texto_cid = f"**CID {cid_codigo}** - **{cid_descricao}**"
            
            analise = f"""📊 **Análise: Dias por Doença**

O {texto_cid} apresenta **{int(top.get('dias_perdidos', 0))} dias perdidos**, representando **{pct:.1f}%** do total.

Esta análise permite identificar as condições de saúde que geram maior impacto em termos de tempo de afastamento, orientando ações preventivas e de gestão de saúde.

💡 **Recomendação**: Desenvolver programa de prevenção específico para as principais causas de afastamento de maior duração."""
            
        elif tipo_grafico == 'escalas':
            if not dados:
                return "⏰ **Análise: Escalas com mais Atestados**\n\nDados ainda não disponíveis para este período."
            
            if isinstance(dados, list) and len(dados) == 0:
                return "⏰ **Análise: Escalas com mais Atestados**\n\nDados ainda não disponíveis para este período."
            
            top = dados[0]
            total = sum(d.get('quantidade', 0) for d in dados)
            pct = (top.get('quantidade', 0) / total * 100) if total > 0 else 0
            
            escala_nome = top.get('escala', 'Não informado')
            if escala_nome == 'N/A' or not escala_nome:
                escala_nome = 'Não informado'
            
            analise = f"""⏰ **Análise: Escalas com mais Atestados**

A escala **{escala_nome}** apresenta o maior número de atestados, com **{top.get('quantidade', 0)} ocorrências ({pct:.1f}% do total)**.

Esta informação pode indicar relação entre horários de trabalho e incidência de afastamentos, possivelmente relacionada a fatores como fadiga, privação de sono ou condições específicas de cada turno.

💡 **Recomendação**: Avaliar condições de trabalho específicas das escalas com maior incidência, considerando ajustes de carga horária, pausas e programas de saúde para trabalhadores em turnos."""
            
        elif tipo_grafico == 'motivos':
            if not dados:
                return "📋 **Análise: Motivos de Incidência**\n\nDados ainda não disponíveis para este período."
            
            if isinstance(dados, list) and len(dados) == 0:
                return "📋 **Análise: Motivos de Incidência**\n\nDados ainda não disponíveis para este período."
            
            top = dados[0]
            total = sum(d.get('quantidade', 0) for d in dados)
            pct = (top.get('quantidade', 0) / total * 100) if total > 0 else 0
            
            motivo_nome = top.get('motivo', 'Não informado')
            if motivo_nome == 'N/A' or not motivo_nome:
                motivo_nome = 'Não informado'
            
            analise = f"""📋 **Análise: Motivos de Incidência**

O motivo **{motivo_nome}** é o principal responsável pelos atestados, com **{pct:.1f}%** das ocorrências ({top.get('quantidade', 0)} de {total} total).

Esta distribuição permite identificar padrões nas causas de afastamento, orientando estratégias de prevenção e gestão de saúde ocupacional.

💡 **Recomendação**: Desenvolver ações preventivas específicas para os principais motivos identificados, com foco em redução de incidência e promoção de saúde."""
            
        elif tipo_grafico == 'centro_custo':
            if not dados:
                return "💰 **Análise: Dias Perdidos por Centro de Custo**\n\nDados ainda não disponíveis para este período."
            
            if isinstance(dados, list) and len(dados) == 0:
                return "💰 **Análise: Dias Perdidos por Centro de Custo**\n\nDados ainda não disponíveis para este período."
            
            top = dados[0]
            total_dias = sum(d.get('dias_perdidos', 0) for d in dados)
            pct = (top.get('dias_perdidos', 0) / total_dias * 100) if total_dias > 0 else 0
            
            # CORREÇÃO: O campo é 'centro_custo', não 'setor'
            setor_nome = top.get('centro_custo', top.get('setor', 'Não informado'))
            if setor_nome == 'N/A' or not setor_nome or setor_nome == 'Não informado':
                # Tenta pegar do campo setor se centro_custo não tiver
                setor_nome = top.get('setor', 'Não informado')
            
            if setor_nome == 'N/A' or not setor_nome:
                setor_nome = 'Não informado'
            
            analise = f"""💰 **Análise: Dias Perdidos por Centro de Custo (Setor)**

O setor **{setor_nome}** apresenta o maior impacto em dias perdidos, com **{int(top.get('dias_perdidos', 0))} dias ({pct:.1f}% do total)**.

Esta análise permite identificar os setores que demandam maior atenção em termos de gestão de absenteísmo e saúde ocupacional.

💡 **Recomendação**: Implementar programa de gestão de saúde ocupacional específico para os setores com maior impacto, incluindo avaliações periódicas e ações preventivas."""
            
        elif tipo_grafico == 'distribuicao_dias':
            if not dados:
                return "📊 **Análise: Distribuição de Dias por Atestado**\n\nDados ainda não disponíveis para este período."
            
            if isinstance(dados, list) and len(dados) == 0:
                return "📊 **Análise: Distribuição de Dias por Atestado**\n\nDados ainda não disponíveis para este período."
            
            # Encontra a faixa mais comum (dados vêm como: [{dias: '1 dia', quantidade: 10}, ...])
            mais_comum = max(dados, key=lambda x: x.get('quantidade', 0))
            total_atestados = sum(d.get('quantidade', 0) for d in dados)
            pct_mais_comum = (mais_comum.get('quantidade', 0) / total_atestados * 100) if total_atestados > 0 else 0
            
            # Calcula média ponderada: extrai número de dias da string (ex: '3-5 dias' -> 4, '1 dia' -> 1)
            def extrair_media_dias(faixa_str):
                if not faixa_str or not isinstance(faixa_str, str):
                    return 0
                # Remove 'dias' e espaços
                faixa_limpa = faixa_str.replace('dias', '').replace('dia', '').strip()
                if '-' in faixa_limpa:
                    # Faixa como '3-5'
                    partes = faixa_limpa.split('-')
                    if len(partes) == 2:
                        try:
                            return (float(partes[0]) + float(partes[1])) / 2
                        except:
                            return 0
                elif '+' in faixa_limpa:
                    # Faixa como '31+'
                    try:
                        return float(faixa_limpa.replace('+', '')) + 5  # Aproximação
                    except:
                        return 0
                else:
                    try:
                        return float(faixa_limpa)
                    except:
                        return 0
            
            media = sum(extrair_media_dias(d.get('dias', '')) * d.get('quantidade', 0) for d in dados) / total_atestados if total_atestados > 0 else 0
            
            dias_faixa = mais_comum.get('dias', 'Não informado')
            if dias_faixa == 'N/A' or not dias_faixa:
                dias_faixa = 'Não informado'
            
            analise = f"""📊 **Análise: Distribuição de Dias por Atestado**

A maioria dos atestados concentra-se na faixa de **{dias_faixa}**, representando **{pct_mais_comum:.1f}%** do total ({mais_comum.get('quantidade', 0)} atestados), com média geral de **{media:.1f} dias por atestado**.

Esta distribuição permite entender o padrão de duração dos afastamentos, orientando estratégias de gestão e acompanhamento.

💡 **Recomendação**: Estabelecer protocolos de acompanhamento diferenciados conforme a duração esperada do afastamento, priorizando casos de maior duração."""
            
        elif tipo_grafico == 'media_cid':
            if not dados:
                return "📊 **Análise: Média de Dias por CID**\n\nDados ainda não disponíveis para este período."
            
            if isinstance(dados, list) and len(dados) == 0:
                return "📊 **Análise: Média de Dias por CID**\n\nDados ainda não disponíveis para este período."
            
            top = dados[0]
            
            # CORREÇÃO: Se descricao = cid (sem diagnóstico), mostra apenas o código
            cid_codigo = top.get('cid', 'N/A')
            cid_descricao = top.get('descricao', top.get('diagnostico', cid_codigo))
            
            if cid_descricao == cid_codigo:
                texto_cid = f"**CID {cid_codigo}**"
            else:
                texto_cid = f"**CID {cid_codigo}** - **{cid_descricao}**"
            
            analise = f"""📊 **Análise: Média de Dias por CID**

O {texto_cid} apresenta a maior média de dias por ocorrência, com **{top.get('media_dias', 0):.1f} dias** em média.

Esta informação permite identificar as condições de saúde que demandam maior tempo de recuperação, orientando estratégias de prevenção e gestão.

💡 **Recomendação**: Desenvolver programa de prevenção específico para as condições com maior média de dias, incluindo ações de promoção de saúde e acompanhamento."""
            
        elif tipo_grafico == 'setor_genero':
            if not dados:
                return "👥 **Análise: Dias Perdidos por Setor e Gênero**\n\nDados ainda não disponíveis para este período."
            
            if isinstance(dados, list) and len(dados) == 0:
                return "👥 **Análise: Dias Perdidos por Setor e Gênero**\n\nDados ainda não disponíveis para este período."
            
            # Dados vêm como: [{setor, genero, dias_perdidos}, ...]
            # Agrupa por setor
            setores_map = {}
            for item in dados:
                setor = item.get('setor', 'Não informado')
                if setor == 'N/A' or not setor:
                    setor = 'Não informado'
                
                genero = item.get('genero', '')
                dias = item.get('dias_perdidos', 0)
                
                if setor not in setores_map:
                    setores_map[setor] = {'M': 0, 'F': 0, 'total': 0}
                
                if genero == 'M':
                    setores_map[setor]['M'] += dias
                elif genero == 'F':
                    setores_map[setor]['F'] += dias
                setores_map[setor]['total'] += dias
            
            # Encontra setor com maior total
            setor_maior = max(setores_map.items(), key=lambda x: x[1]['total'])
            setor_nome = setor_maior[0]
            valores = setor_maior[1]
            
            total_geral = sum(s['total'] for s in setores_map.values())
            pct_setor = (valores['total'] / total_geral * 100) if total_geral > 0 else 0
            
            analise = f"""👥 **Análise: Dias Perdidos por Setor e Gênero**

O setor **{setor_nome}** apresenta o maior impacto total, com **{int(valores['total'])} dias perdidos ({pct_setor:.1f}% do total)**, distribuídos em **{int(valores['M'])} dias (Masculino)** e **{int(valores['F'])} dias (Feminino)**.

Esta análise permite identificar padrões específicos por setor e gênero, orientando ações preventivas direcionadas considerando as particularidades de cada grupo.

💡 **Recomendação**: Investigar causas específicas observadas no setor e desenvolver ações preventivas considerando as diferenças entre gêneros, incluindo programas de saúde ocupacional direcionados."""
        
        elif tipo_grafico == 'tempo_servico_atestados':
            if not dados or len(dados) == 0:
                return "Não há dados suficientes para análise."
            
            # Encontra faixa com mais dias
            faixa_mais_dias = max(dados, key=lambda x: x.get('dias_afastamento', 0))
            total_dias = sum(d.get('dias_afastamento', 0) for d in dados)
            pct = (faixa_mais_dias.get('dias_afastamento', 0) / total_dias * 100) if total_dias > 0 else 0
            
            faixa_tempo = faixa_mais_dias.get('faixa_tempo_servico', 'Não informado')
            if faixa_tempo == 'N/A' or not faixa_tempo:
                faixa_tempo = 'Não informado'
            
            analise = f"""⏱️ **Análise: Tempo Serviço x Atestados**

Funcionários com **{faixa_tempo}** de empresa apresentam o maior índice de dias de afastamento, com **{int(faixa_mais_dias.get('dias_afastamento', 0))} dias ({pct:.1f}% do total)** e **{faixa_mais_dias.get('quantidade_atestados', 0)} atestados**.

Esta análise permite identificar se funcionários mais antigos (com mais tempo na empresa) ou mais novos (recém-admitidos) apresentam maior incidência de atestados.

💡 **Recomendação**: Desenvolver programas de saúde ocupacional específicos conforme o tempo de serviço, considerando as necessidades de cada grupo (integração para novos funcionários, prevenção de doenças ocupacionais para funcionários mais antigos)."""
        
        elif tipo_grafico == 'classificacao_funcionarios_ro':
            if not dados or len(dados) == 0:
                return "Não há dados suficientes para análise."
            
            top = dados[0]
            top5_total = sum(d.get('quantidade', 0) for d in dados[:5])
            total_dias = metricas.get('total_dias_perdidos', 0) if metricas else top5_total
            pct_top5 = (top5_total / total_dias * 100) if total_dias > 0 else 0
            
            nome_funcionario = top.get('nome', 'Não informado')
            if nome_funcionario == 'N/A' or not nome_funcionario:
                nome_funcionario = 'Não informado'
            
            analise = f"""👤 **Análise: Classificação por Funcionário**

O funcionário **{nome_funcionario}** apresenta **{int(top.get('quantidade', 0))} dias de atestados**, representando o maior índice individual de afastamento.

Os **5 funcionários com maior incidência** concentram **{pct_top5:.1f}%** do total de dias perdidos, indicando necessidade de foco em ações preventivas específicas para este grupo.

💡 **Recomendação**: Implementar programa de acompanhamento individualizado para funcionários com alto índice de absenteísmo, incluindo avaliação de saúde ocupacional e apoio multidisciplinar."""
        
        elif tipo_grafico == 'classificacao_setores_ro':
            if not dados or len(dados) == 0:
                return "Não há dados suficientes para análise."
            
            top = dados[0]
            total_dias = sum(d.get('dias_afastamento', 0) for d in dados)
            pct = (top.get('dias_afastamento', 0) / total_dias * 100) if total_dias > 0 else 0
            
            setor_nome = top.get('setor', 'Não informado')
            if setor_nome == 'N/A' or not setor_nome:
                setor_nome = 'Não informado'
            
            analise = f"""🏢 **Análise: Classificação por Setor**

O setor **{setor_nome}** apresenta o maior índice de dias de afastamento, com **{int(top.get('dias_afastamento', 0))} dias ({pct:.1f}% do total)**.

Esta concentração pode indicar questões específicas relacionadas a condições de trabalho, carga horária, ergonomia ou fatores organizacionais deste setor.

💡 **Recomendação**: Realizar avaliação detalhada das condições de trabalho no setor, incluindo análise ergonômica, gestão de carga de trabalho e programa de saúde ocupacional específico."""
        
        elif tipo_grafico == 'classificacao_doencas_ro':
            # NOVA ANÁLISE - GARANTE 100% SINCRONIZAÇÃO COM O GRÁFICO
            try:
                # Validação inicial
                if not dados:
                    return "Não há dados suficientes para análise."
                
                # Converte para lista se necessário
                if isinstance(dados, dict):
                    dados_lista = [dados]
                elif isinstance(dados, list):
                    dados_lista = dados.copy()  # Cópia para não modificar original
                else:
                    dados_lista = list(dados) if dados else []
                
                if len(dados_lista) == 0:
                    return "Não há dados suficientes para análise."
                
                # ORDENA EXATAMENTE COMO O GRÁFICO FAZ (por quantidade decrescente)
                # Usa a mesma lógica do frontend: sort((a, b) => (b.quantidade || 0) - (a.quantidade || 0))
                dados_ordenados = sorted(
                    dados_lista,
                    key=lambda x: float(x.get('quantidade', 0) or 0),
                    reverse=True
                )
                
                # Pega o TOP 1 (mesmo que o gráfico mostra no topo)
                top_doenca = dados_ordenados[0] if dados_ordenados else None
                
                if not top_doenca:
                    return "Não há dados suficientes para análise."
                
                # Extrai dados da doença do topo
                nome_doenca = top_doenca.get('tipo_doenca', 'Não informado')
                dias_doenca = float(top_doenca.get('quantidade', 0) or 0)
                
                # Calcula total de dias de TODAS as doenças (mesmo conjunto do gráfico)
                total_dias_todas = sum(float(d.get('quantidade', 0) or 0) for d in dados_ordenados)
                
                # Calcula percentual
                percentual = (dias_doenca / total_dias_todas * 100) if total_dias_todas > 0 else 0
                
                # Pega TOP 3 para contexto
                top3 = dados_ordenados[:3]
                top3_info = []
                for i, doenca in enumerate(top3, 1):
                    nome = doenca.get('tipo_doenca', 'N/A')
                    dias = float(doenca.get('quantidade', 0) or 0)
                    pct_item = (dias / total_dias_todas * 100) if total_dias_todas > 0 else 0
                    top3_info.append(f"{i}º: {nome} ({int(dias)} dias, {pct_item:.1f}%)")
                
                print(f"[ANALISE DOENÇAS] ===== INÍCIO =====")
                print(f"[ANALISE DOENÇAS] Total de doenças recebidas: {len(dados_lista)}")
                print(f"[ANALISE DOENÇAS] Doença TOP 1: {nome_doenca} - {int(dias_doenca)} dias ({percentual:.1f}%)")
                print(f"[ANALISE DOENÇAS] Total de dias (todas doenças): {int(total_dias_todas)}")
                print(f"[ANALISE DOENÇAS] TOP 3: {', '.join(top3_info)}")
                print(f"[ANALISE DOENÇAS] ===== FIM =====")
                
                # GERA ANÁLISE COMPLETA E PRECISA
                analise = f"""🩺 **Análise: Classificação por Doença**

**Doença com Maior Impacto:**
A doença **{nome_doenca}** apresenta o maior número de dias de afastamento, com **{int(dias_doenca)} dias**, representando **{percentual:.1f}%** do total de dias perdidos por todas as doenças analisadas.

**Contexto:**
- Total de dias perdidos (todas doenças): **{int(total_dias_todas)} dias**
- Doenças analisadas: **{len(dados_ordenados)}**
- TOP 3 doenças concentram: **{sum(float(d.get('quantidade', 0) or 0) for d in top3) / total_dias_todas * 100 if total_dias_todas > 0 else 0:.1f}%** dos dias perdidos

**Interpretação:**
Esta análise identifica as condições de saúde que geram maior impacto em termos de tempo de afastamento, permitindo direcionar ações preventivas e de gestão de saúde ocupacional de forma estratégica.

💡 **Recomendação**: Desenvolver programa de prevenção específico para **{nome_doenca}**, incluindo ações educativas, avaliações preventivas e acompanhamento médico especializado."""
                
                return analise
                
            except Exception as e:
                import traceback
                print(f"[ANALISE DOENÇAS] ERRO ao gerar análise: {e}")
                traceback.print_exc()
                return f"Erro ao gerar análise: {str(e)}"
        
        elif tipo_grafico == 'dias_ano_coerencia':
            if not dados:
                return "Não há dados suficientes para análise."
            
            # Usa dados mensais se disponíveis, senão usa anuais
            usar_mensal = dados.get('meses') and len(dados.get('meses', [])) > 0
            coerente_total = sum(dados.get('coerente_mensal', dados.get('coerente', [])) or [])
            sem_coerencia_total = sum(dados.get('sem_coerencia_mensal', dados.get('sem_coerencia', [])) or [])
            total = coerente_total + sem_coerencia_total
            pct_coerente = (coerente_total / total * 100) if total > 0 else 0
            pct_sem_coerencia = (sem_coerencia_total / total * 100) if total > 0 else 0
            
            analise = f"""📊 **Análise: Dias Atestados por Ano - Coerência**

A análise de coerência mostra que **{pct_coerente:.1f}% dos dias ({int(coerente_total)} dias)** são de atestados **coerentes**, enquanto **{pct_sem_coerencia:.1f}% ({int(sem_coerencia_total)} dias)** são **sem coerência**.

Esta análise permite identificar a qualidade e consistência dos atestados, orientando ações de gestão e controle.

💡 **Recomendação**: Investigar causas dos atestados sem coerência e implementar ações para melhorar a qualidade e consistência dos registros."""
        
        elif tipo_grafico == 'analise_coerencia':
            if not dados or dados.get('total', 0) == 0:
                return "Não há dados suficientes para análise."
            
            pct_coerente = dados.get('percentual_coerente', 0)
            pct_sem_coerencia = dados.get('percentual_sem_coerencia', 0)
            
            analise = f"""📊 **Análise: Análise Atestados - Coerência**

A análise de coerência mostra que **{pct_coerente:.1f}% dos dias ({int(dados.get('coerente', 0))} dias)** são de atestados **coerentes**, enquanto **{pct_sem_coerencia:.1f}% ({int(dados.get('sem_coerencia', 0))} dias)** são **sem coerência**.

Esta distribuição permite identificar a qualidade e consistência dos atestados, orientando ações de gestão e controle.

💡 **Recomendação**: Investigar causas dos atestados sem coerência e implementar ações para melhorar a qualidade e consistência dos registros."""
        
        elif tipo_grafico == 'frequencia_atestados':
            # Dados vêm como: [{frequencia: '1 atestado', quantidade: 10}, ...]
            if not dados or len(dados) == 0:
                return "Não há dados suficientes para análise."
            
            total_funcionarios = sum(d.get('quantidade', 0) for d in dados)
            mais_comum = max(dados, key=lambda x: x.get('quantidade', 0))
            pct_mais_comum = (mais_comum.get('quantidade', 0) / total_funcionarios * 100) if total_funcionarios > 0 else 0
            
            # Calcula funcionários com múltiplos atestados (3+)
            multiplos = sum(d.get('quantidade', 0) for d in dados if '3' in d.get('frequencia', '') or '6' in d.get('frequencia', '') or '11' in d.get('frequencia', ''))
            pct_multiplos = (multiplos / total_funcionarios * 100) if total_funcionarios > 0 else 0
            
            frequencia_nome = mais_comum.get('frequencia', 'Não informado')
            if frequencia_nome == 'N/A' or not frequencia_nome:
                frequencia_nome = 'Não informado'
            
            analise = f"""📊 **Análise: Frequência de Atestados por Funcionário**

A maioria dos funcionários ({mais_comum.get('quantidade', 0)} funcionários, {pct_mais_comum:.1f}%) apresenta **{frequencia_nome}** no período analisado.

**{pct_multiplos:.1f}% dos funcionários ({multiplos} funcionários)** apresentam **3 ou mais atestados**, indicando necessidade de atenção especial para este grupo.

Esta distribuição permite identificar funcionários com padrão recorrente de afastamentos, orientando ações preventivas e de acompanhamento individualizado.

💡 **Recomendação**: Implementar programa de acompanhamento para funcionários com múltiplos atestados, incluindo avaliação de saúde ocupacional, análise de causas e ações preventivas direcionadas."""
        
        elif tipo_grafico == 'comparativo_dias_horas':
            # Dados vêm como: [{setor, dias_perdidos, horas_perdidas}, ...]
            if not dados:
                return "📊 **Análise: Comparativo Dias vs Horas Perdidas**\n\nDados ainda não disponíveis para este período."
            
            if isinstance(dados, list) and len(dados) == 0:
                return "📊 **Análise: Comparativo Dias vs Horas Perdidas**\n\nDados ainda não disponíveis para este período."
            
            # Encontra setor com maior impacto (considera dias + horas convertidas)
            setor_maior = max(dados, key=lambda x: (x.get('dias_perdidos', 0) + (x.get('horas_perdidas', 0) / 8)))
            total_dias = sum(d.get('dias_perdidos', 0) for d in dados)
            total_horas = sum(d.get('horas_perdidas', 0) for d in dados)
            
            pct_dias = (setor_maior.get('dias_perdidos', 0) / total_dias * 100) if total_dias > 0 else 0
            pct_horas = (setor_maior.get('horas_perdidas', 0) / total_horas * 100) if total_horas > 0 else 0
            
            # Converte horas para dias equivalentes (8 horas = 1 dia)
            horas_equivalente = setor_maior.get('horas_perdidas', 0) / 8
            dias_totais_equivalente = setor_maior.get('dias_perdidos', 0) + horas_equivalente
            
            # Converte total de horas para dias equivalentes
            total_horas_equivalente = total_horas / 8
            total_geral_equivalente = total_dias + total_horas_equivalente
            
            setor_nome = setor_maior.get('setor', 'Não informado')
            if setor_nome == 'N/A' or not setor_nome:
                setor_nome = 'Não informado'
            
            analise = f"""📊 **Análise: Comparativo Dias vs Horas Perdidas**

O setor **{setor_nome}** apresenta o maior impacto combinado:
- **{int(setor_maior.get('dias_perdidos', 0))} dias perdidos** ({pct_dias:.1f}% do total de dias)
- **{int(setor_maior.get('horas_perdidas', 0))} horas perdidas** ({pct_horas:.1f}% do total de horas)
- **Total equivalente: {dias_totais_equivalente:.1f} dias** (dias + horas convertidas)

**Total geral do período:**
- {int(total_dias)} dias perdidos
- {int(total_horas)} horas perdidas (equivalente a {total_horas_equivalente:.1f} dias)
- **Total geral: {total_geral_equivalente:.1f} dias equivalentes**

Esta análise permite identificar setores que demandam maior atenção tanto em afastamentos completos (dias) quanto em afastamentos parciais (horas), orientando estratégias de gestão diferenciadas.

💡 **Recomendação**: Implementar programa de gestão de absenteísmo específico para o setor, considerando tanto afastamentos completos quanto parciais, com foco em prevenção e acompanhamento."""
        
        else:
            analise = "Análise não disponível para este tipo de gráfico."
        
        return analise


