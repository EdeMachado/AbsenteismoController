"""
Excel processor - Lê e processa planilhas de atestados
"""
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
import re
import json
from collections import OrderedDict
from difflib import SequenceMatcher
from .genero_detector import GeneroDetector

class ExcelProcessor:
    """Processador de planilhas Excel"""
    
    # Mapeamento semântico de campos do sistema para variações comuns
    CAMPOS_SISTEMA = {
        'nomecompleto': ['nome', 'completo', 'funcionario', 'funcionário', 'empregado', 'colaborador'],
        'setor': ['setor', 'departamento', 'depto', 'area', 'área', 'centro', 'custo'],
        'dias_atestados': ['dias', 'atestado', 'atestados', 'afastamento', 'afastamentos'],
        'cid': ['cid', 'codigo', 'código', 'diagnostico', 'diagnóstico'],
        'data_do_atestado': ['data', 'atestado', 'emissao', 'emissão', 'entrega'],
        'horas_perdi': ['horas', 'perdidas', 'perdi', 'perdido', 'ausencia', 'ausência']
    }
    
    def __init__(self, file_path: str, custom_mapping: Dict[str, str] = None):
        """
        Args:
            file_path: Caminho do arquivo Excel
            custom_mapping: Dicionário com mapeamento customizado de colunas
                          Ex: {"NOME_FUNC": "nomecompleto", "DEPARTAMENTO": "setor"}
        """
        self.file_path = file_path
        self.df = None
        self.dados_processados = []
        self.custom_mapping = custom_mapping or {}  # Mapeamento customizado do cliente
        
    def ler_planilha(self) -> bool:
        """Lê a planilha Excel"""
        try:
            # Tenta diferentes encodings
            self.df = pd.read_excel(self.file_path, sheet_name=0, engine='openpyxl')
            return True
        except Exception as e:
            print(f"Erro ao ler planilha: {e}")
            return False
    
    def padronizar_colunas(self):
        """Padroniza nomes das colunas da planilha padronizada"""
        # Mantém os nomes originais das colunas, apenas normaliza espaços
        self.df.columns = self.df.columns.str.strip()
        
        # Se houver mapeamento customizado, aplica primeiro
        if self.custom_mapping:
            print(f"🔧 Aplicando mapeamento customizado: {self.custom_mapping}")
            print(f"📊 Colunas originais da planilha: {list(self.df.columns)}")
            
            # Cria mapeamento reverso: coluna da planilha -> campo normalizado
            mapeamento_custom = {}
            colunas_mapeadas = set()
            
            for col_planilha, campo_sistema in self.custom_mapping.items():
                # Procura a coluna na planilha (case-insensitive, remove espaços extras)
                col_planilha_limpa = col_planilha.strip()
                encontrada = False
                
                # Normaliza o nome da coluna procurada (remove espaços, acentos, etc)
                col_planilha_norm = self._normalizar_nome_coluna(col_planilha_limpa)
                
                # Primeiro tenta match exato (case-insensitive)
                for col_atual in self.df.columns:
                    if col_atual in colunas_mapeadas:
                        continue
                    col_atual_limpa = col_atual.strip()
                    # Compara normalizado (sem espaços, acentos, case)
                    col_atual_norm = self._normalizar_nome_coluna(col_atual_limpa)
                    if col_atual_norm == col_planilha_norm:
                        mapeamento_custom[col_atual] = campo_sistema.upper()
                        colunas_mapeadas.add(col_atual)
                        print(f"  ✅ Mapeado (exato normalizado): '{col_atual}' -> '{campo_sistema.upper()}' (procurando '{col_planilha}')")
                        encontrada = True
                        break
                    # Também tenta match direto case-insensitive
                    elif col_atual_limpa.upper() == col_planilha_limpa.upper():
                        mapeamento_custom[col_atual] = campo_sistema.upper()
                        colunas_mapeadas.add(col_atual)
                        print(f"  ✅ Mapeado (exato): '{col_atual}' -> '{campo_sistema.upper()}'")
                        encontrada = True
                        break
                
                # Se não encontrou exato, tenta fuzzy matching
                if not encontrada:
                    melhor_match = self._encontrar_coluna_similar(col_planilha_limpa, [c for c in self.df.columns if c not in colunas_mapeadas])
                    if melhor_match and melhor_match[1] > 0.6:  # Threshold reduzido para 60% de similaridade
                        col_atual = melhor_match[0]
                        mapeamento_custom[col_atual] = campo_sistema.upper()
                        colunas_mapeadas.add(col_atual)
                        print(f"  ✅ Mapeado (fuzzy {melhor_match[1]:.0%}): '{col_atual}' -> '{campo_sistema.upper()}' (procurando '{col_planilha}')")
                        encontrada = True
                
                if not encontrada:
                    print(f"  ⚠️ Coluna '{col_planilha}' não encontrada na planilha")
                    print(f"     Colunas disponíveis: {list(self.df.columns)}")
            
            # Aplica mapeamento customizado
            if mapeamento_custom:
                self.df.rename(columns=mapeamento_custom, inplace=True)
                print(f"📊 Colunas após mapeamento: {list(self.df.columns)}")
            else:
                print("⚠️ Nenhuma coluna foi mapeada!")
        
        # Mapeamento padrão (fallback para colunas não mapeadas)
        # Inclui variações comuns de nomes de colunas
        mapeamento_padrao = {
            'NOMECOMPLETO': 'NOMECOMPLETO',
            'NOME COMPLETO': 'NOMECOMPLETO',  # Variação com espaço
            'NOME_COMPLETO': 'NOMECOMPLETO',  # Variação com underscore
            'NOMEFUNCIONARIO': 'NOMECOMPLETO',
            'NOME FUNCIONARIO': 'NOMECOMPLETO',
            'NOME_FUNCIONARIO': 'NOMECOMPLETO',
            'FUNCIONARIO': 'NOMECOMPLETO',
            'FUNCIONÁRIO': 'NOMECOMPLETO',
            'DESCRIÇÃO ATESTAD': 'DESCRICAO_ATESTAD',
            'DESCRICAO ATESTAD': 'DESCRICAO_ATESTAD',
            'DESCRIÇÃO ATESTADO': 'DESCRICAO_ATESTAD',
            'DESCRICAO ATESTADO': 'DESCRICAO_ATESTAD',
            'DIAS ATESTADOS': 'DIAS_ATESTADOS',
            'DIAS_ATESTADOS': 'DIAS_ATESTADOS',
            'DIAS': 'DIAS_ATESTADOS',
            'CID': 'CID',
            'CID-10': 'CID',
            'DIAGNÓSTICO': 'DIAGNOSTICO',
            'DIAGNOSTICO': 'DIAGNOSTICO',
            'CENTROCUST': 'CENTRO_CUSTO',
            'CENTRO CUSTO': 'CENTRO_CUSTO',
            'CENTROCUSTO': 'CENTRO_CUSTO',
            'setor': 'SETOR',
            'SETOR': 'SETOR',
            'DEPARTAMENTO': 'SETOR',
            'motivo atestado': 'MOTIVO_ATESTADO',
            'MOTIVO ATESTADO': 'MOTIVO_ATESTADO',
            'escala': 'ESCALA',
            'ESCALA': 'ESCALA',
            'Horas/dia': 'HORAS_DIA',
            'HORAS/DIA': 'HORAS_DIA',
            'Horas perdi': 'HORAS_PERDI',
            'HORAS PERDI': 'HORAS_PERDI',
            'HORAS PERDIDAS': 'HORAS_PERDI',
            'Horas perdidas': 'HORAS_PERDI',
        }
        
        # Renomeia as colunas não mapeadas para formato padronizado
        mapeamento_custom_keys = set(mapeamento_custom.keys()) if self.custom_mapping else set()
        for col_atual in self.df.columns:
            col_normalizada = col_atual.strip()
            # Se já foi mapeada pelo custom_mapping, pula
            if col_atual in mapeamento_custom_keys:
                continue
            # Aplica mapeamento padrão (case-insensitive)
            col_upper = col_normalizada.upper()
            if col_upper in mapeamento_padrao:
                self.df.rename(columns={col_atual: mapeamento_padrao[col_upper]}, inplace=True)
                print(f"  🔄 Mapeamento padrão: '{col_atual}' -> '{mapeamento_padrao[col_upper]}'")
            else:
                # Se não estiver no mapeamento, normaliza para maiúsculas com underscore
                col_nova = col_normalizada.upper().replace(' ', '_').replace('/', '_').replace('-', '_')
                if col_nova != col_normalizada:
                    self.df.rename(columns={col_atual: col_nova}, inplace=True)
    
    def _encontrar_coluna_similar(self, coluna_procurada: str, colunas_disponiveis: List[str], threshold: float = 0.6) -> Optional[Tuple[str, float]]:
        """
        Encontra a coluna mais similar usando fuzzy matching
        
        Args:
            coluna_procurada: Nome da coluna que estamos procurando
            colunas_disponiveis: Lista de colunas disponíveis na planilha
            threshold: Similaridade mínima (0-1)
        
        Returns:
            Tupla (nome_coluna, similaridade) ou None se não encontrar
        """
        if not colunas_disponiveis:
            return None
        
        coluna_procurada_norm = self._normalizar_nome_coluna(coluna_procurada)
        melhor_match = None
        melhor_score = 0.0
        
        for coluna in colunas_disponiveis:
            coluna_norm = self._normalizar_nome_coluna(coluna)
            
            # Se normalizados são iguais, é match perfeito
            if coluna_procurada_norm == coluna_norm:
                return (coluna, 1.0)
            
            # Calcula similaridade usando SequenceMatcher
            score = SequenceMatcher(None, coluna_procurada_norm, coluna_norm).ratio()
            
            # Bonus se uma contém a outra (ex: "NOMECOMPLETO" contém "NOME" e "COMPLETO")
            if coluna_procurada_norm in coluna_norm or coluna_norm in coluna_procurada_norm:
                score = min(1.0, score + 0.3)
            
            # Bonus extra se palavras-chave importantes coincidem
            palavras_procurada = set(coluna_procurada_norm.split()) if ' ' in coluna_procurada else {coluna_procurada_norm}
            palavras_coluna = set(coluna_norm.split()) if ' ' in coluna_norm else {coluna_norm}
            palavras_comuns = palavras_procurada.intersection(palavras_coluna)
            if palavras_comuns and len(palavras_comuns) >= len(palavras_procurada) * 0.5:
                score = min(1.0, score + 0.2)
            
            if score > melhor_score:
                melhor_score = score
                melhor_match = coluna
        
        if melhor_score >= threshold:
            return (melhor_match, melhor_score)
        return None
    
    def _normalizar_nome_coluna(self, nome: str) -> str:
        """
        Normaliza nome de coluna para comparação (remove acentos, espaços, case)
        """
        # Remove acentos básicos
        nome = nome.upper().strip()
        nome = nome.replace('Á', 'A').replace('À', 'A').replace('Â', 'A').replace('Ã', 'A')
        nome = nome.replace('É', 'E').replace('Ê', 'E')
        nome = nome.replace('Í', 'I')
        nome = nome.replace('Ó', 'O').replace('Ô', 'O').replace('Õ', 'O')
        nome = nome.replace('Ú', 'U')
        nome = nome.replace('Ç', 'C')
        # Remove espaços e caracteres especiais
        nome = re.sub(r'[^A-Z0-9]', '', nome)
        return nome
    
    def limpar_dados(self):
        """Limpa e valida os dados"""
        # Remove linhas completamente vazias
        self.df.dropna(how='all', inplace=True)
        
        # Converte para string e limpa
        for col in ['NOME_FUNCIONARIO', 'SETOR', 'DESCRICAO_CID']:
            if col in self.df.columns:
                try:
                    self.df[col] = self.df[col].fillna('').astype(str).str.replace(r'\n.*', '', regex=True).str.strip()
                    # Corrige encoding de caracteres especiais comuns
                    self.df[col] = self.df[col].str.replace('??', 'ã').str.replace('??', 'é').str.replace('??', 'í').str.replace('??', 'ó').str.replace('??', 'ú').str.replace('??', 'ç').str.replace('??', 'á').str.replace('??', 'ê').str.replace('??', 'ô').str.replace('??', 'õ')
                except:
                    # Se der erro, deixa como string simples
                    self.df[col] = self.df[col].fillna('').astype(str)
        
        # Preenche valores nulos com padrões
        colunas_texto = ['NOME_FUNCIONARIO', 'SETOR', 'CARGO', 'TIPO_ATESTADO', 'CID', 'DESCRICAO_CID']
        for col in colunas_texto:
            if col in self.df.columns:
                self.df[col] = self.df[col].fillna('')
        
        # Colunas numéricas
        colunas_numero = ['NUMERO_DIAS_ATESTADO', 'NUMERO_HORAS_ATESTADO', 'HORAS_PERDIDAS']
        for col in colunas_numero:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)
        
        # Converte datas
        colunas_data = ['DATA_AFASTAMENTO', 'DATA_RETORNO']
        for col in colunas_data:
            if col in self.df.columns:
                self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
    
    def calcular_metricas(self):
        """Calcula métricas adicionais"""
        # Dias perdidos = NUMERO_DIAS_ATESTADO
        if 'NUMERO_DIAS_ATESTADO' in self.df.columns:
            self.df['DIAS_PERDIDOS'] = self.df['NUMERO_DIAS_ATESTADO']
        
        # Horas perdidas (já vem calculado na planilha ou calculamos)
        if 'HORAS_PERDIDAS' not in self.df.columns:
            # Se não tiver, calcula: dias * 8 horas + horas avulsas
            dias_em_horas = self.df.get('NUMERO_DIAS_ATESTADO', 0) * 8
            horas_avulsas = self.df.get('NUMERO_HORAS_ATESTADO', 0)
            self.df['HORAS_PERDIDAS'] = dias_em_horas + horas_avulsas
    
    def processar(self) -> List[Dict[str, Any]]:
        """Processa a planilha completa"""
        if not self.ler_planilha():
            return []
        
        # Guarda os nomes originais das colunas ANTES de qualquer processamento
        # IMPORTANTE: mantém a ordem original
        self.colunas_originais = list(self.df.columns)
        
        # Cria um mapeamento de colunas originais para normalizadas (para buscar valores)
        # Guarda o DataFrame original ANTES de normalizar
        self.df_original = self.df.copy()
        
        self.padronizar_colunas()
        
        # Debug: mostra colunas após padronização
        print(f"📊 Colunas após padronização: {list(self.df.columns)}")
        
        # Após padronizar, cria mapeamento das colunas originais para normalizadas
        mapeamento_colunas = {}
        for col_original in self.colunas_originais:
            # Encontra a coluna normalizada correspondente
            col_normalizada = None
            # Tenta encontrar pelo nome original (pode ter sido renomeada)
            if col_original in self.df.columns:
                col_normalizada = col_original
            else:
                # Procura na lista de colunas normalizadas
                for col_df in self.df.columns:
                    # Compara sem case e sem espaços/underscores
                    orig_clean = col_original.upper().strip().replace(' ', '_').replace('/', '_')
                    df_clean = col_df.upper().strip().replace(' ', '_').replace('/', '_')
                    if orig_clean == df_clean:
                        col_normalizada = col_df
                        break
            mapeamento_colunas[col_original] = col_normalizada if col_normalizada else col_original
        
        self.limpar_dados()
        self.calcular_metricas()
        
        # Converte para lista de dicionários
        registros = []
        
        for idx, (_, row) in enumerate(self.df.iterrows()):
            # Detecta gênero pelo nome se não tiver coluna GENERO
            genero = ''
            nome_para_genero = str(row.get('NOMECOMPLETO', '')) or str(row.get('NOME_FUNCIONARIO', ''))
            if nome_para_genero:
                genero = GeneroDetector.detectar(nome_para_genero)
            
            # Salva TODAS as colunas originais da planilha em um JSON
            # MANTÉM A ORDEM ORIGINAL DAS COLUNAS
            # Busca valores no DataFrame ORIGINAL (antes de normalizar)
            dados_originais_dict = OrderedDict()  # Usa OrderedDict para manter ordem
            for col_original in self.colunas_originais:
                # Busca o valor no DataFrame original (pelo índice da linha)
                try:
                    # Pega o valor da linha original usando o índice
                    row_original = self.df_original.iloc[idx]
                    valor = row_original[col_original] if col_original in row_original.index else None
                except:
                    # Se der erro, tenta buscar na coluna normalizada
                    try:
                        col_busca = mapeamento_colunas.get(col_original, col_original)
                        if col_busca and col_busca in self.df.columns:
                            valor = row.get(col_busca)
                        else:
                            valor = None
                    except:
                        valor = None
                
                # Converte valores para tipos Python nativos (serializável em JSON)
                if valor is None or (isinstance(valor, (int, float)) and pd.isna(valor)):
                    dados_originais_dict[col_original] = None
                elif isinstance(valor, pd.Timestamp):
                    dados_originais_dict[col_original] = valor.strftime('%Y-%m-%d') if not pd.isna(valor) else None
                elif isinstance(valor, (int, float)):
                    dados_originais_dict[col_original] = float(valor) if not pd.isna(valor) else None
                else:
                    dados_originais_dict[col_original] = str(valor) if valor is not None else None
            
            # Mapeia campos da planilha padronizada - busca valores nas colunas normalizadas
            def get_valor(col_normalizada, default=''):
                if not col_normalizada:
                    return default
                
                # Tenta match exato primeiro (case-insensitive)
                for col_df in self.df.columns:
                    if col_df.upper().strip() == col_normalizada.upper().strip():
                        valor = row.get(col_df)
                        if valor is not None and pd.notna(valor) and str(valor).strip():
                            return valor
                
                # Se não encontrou, tenta variações do nome (sem espaços/underscores/hífens)
                col_upper_clean = col_normalizada.upper().replace(' ', '').replace('_', '').replace('-', '')
                for col_df in self.df.columns:
                    col_df_clean = col_df.upper().replace(' ', '').replace('_', '').replace('-', '')
                    if col_df_clean == col_upper_clean:
                        valor = row.get(col_df)
                        if valor is not None and pd.notna(valor) and str(valor).strip():
                            return valor
                
                # Para NOMECOMPLETO, tenta variações específicas
                if col_normalizada.upper() == 'NOMECOMPLETO':
                    variacoes = ['NOME COMPLETO', 'NOME_COMPLETO', 'NOMEFUNCIONARIO', 'NOME FUNCIONARIO', 'NOME_FUNCIONARIO', 'FUNCIONARIO', 'FUNCIONÁRIO']
                    for variacao in variacoes:
                        for col_df in self.df.columns:
                            if col_df.upper().strip() == variacao.upper().strip():
                                valor = row.get(col_df)
                                if valor is not None and pd.notna(valor) and str(valor).strip():
                                    print(f"  ✅ Encontrado '{col_df}' como variação de NOMECOMPLETO")
                                    return valor
                
                # Tenta fuzzy matching como último recurso
                melhor_match = self._encontrar_coluna_similar(col_normalizada, list(self.df.columns), threshold=0.75)
                if melhor_match:
                    valor = row.get(melhor_match[0])
                    if valor is not None and pd.notna(valor) and str(valor).strip():
                        return valor
                
                return default
            
            def get_valor_float(col_normalizada, default=0):
                val = get_valor(col_normalizada, None)
                if val is not None and pd.notna(val):
                    try:
                        return float(val)
                    except:
                        return default
                return default
            
            # Debug: verifica se NOMECOMPLETO existe
            if idx == 0:  # Apenas na primeira linha para não poluir logs
                print(f"🔍 Verificando colunas disponíveis para primeira linha:")
                print(f"   Colunas no DataFrame: {list(self.df.columns)}")
                print(f"   Procurando por 'NOMECOMPLETO': {'NOMECOMPLETO' in self.df.columns}")
                valor_nome = get_valor('NOMECOMPLETO', '')
                print(f"   Valor encontrado para NOMECOMPLETO: '{valor_nome}'")
            
            registro = {
                # Campos principais da planilha padronizada
                'nomecompleto': str(get_valor('NOMECOMPLETO', '')),
                'descricao_atestad': str(get_valor('DESCRICAO_ATESTAD', '')),
                'dias_atestados': get_valor_float('DIAS_ATESTADOS', 0),
                'cid': str(get_valor('CID', '')),
                'diagnostico': str(get_valor('DIAGNOSTICO', '')),
                'centro_custo': str(get_valor('CENTRO_CUSTO', '')),
                'setor': str(get_valor('SETOR', '')),
                'motivo_atestado': str(get_valor('MOTIVO_ATESTADO', '')),
                'escala': str(get_valor('ESCALA', '')),
                'horas_dia': get_valor_float('HORAS_DIA', 0),
                'horas_perdi': get_valor_float('HORAS_PERDI', 0),
                
                # Campos legados (para compatibilidade)
                'nome_funcionario': str(get_valor('NOMECOMPLETO', '')),
                'cpf': str(get_valor('CPF', '')),
                'matricula': str(get_valor('MATRICULA', '')),
                'cargo': str(get_valor('CARGO', '')),
                'genero': genero,
                'data_afastamento': get_valor('DATA_AFASTAMENTO', None),
                'data_retorno': get_valor('DATA_RETORNO', None),
                'tipo_info_atestado': int(get_valor_float('TIPO_INFO_ATESTADO', 0)) if get_valor('TIPO_INFO_ATESTADO', None) else None,
                'tipo_atestado': str(get_valor('TIPO_ATESTADO', '')),
                'descricao_cid': str(get_valor('DIAGNOSTICO', '')),
                'numero_dias_atestado': get_valor_float('DIAS_ATESTADOS', 0),
                'numero_horas_atestado': get_valor_float('HORAS_DIA', 0),
                'dias_perdidos': get_valor_float('DIAS_ATESTADOS', 0),
                'horas_perdidas': get_valor_float('HORAS_PERDI', 0),
                
                # Salva dados originais com TODAS as colunas na ordem original
                'dados_originais': json.dumps(dados_originais_dict, ensure_ascii=False, default=str),
            }
            registros.append(registro)
        
        return registros
    
    def exportar_tratado(self, output_path: str) -> bool:
        """Exporta planilha tratada"""
        try:
            self.df.to_excel(output_path, index=False)
            return True
        except Exception as e:
            print(f"Erro ao exportar: {e}")
            return False
