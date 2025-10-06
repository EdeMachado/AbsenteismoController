"""
Excel processor - Lê e processa planilhas de atestados
"""
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
import re

class ExcelProcessor:
    """Processador de planilhas Excel"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.df = None
        self.dados_processados = []
        
    def ler_planilha(self) -> bool:
        """Lê a planilha Excel"""
        try:
            self.df = pd.read_excel(self.file_path, sheet_name=0)
            return True
        except Exception as e:
            print(f"Erro ao ler planilha: {e}")
            return False
    
    def padronizar_colunas(self):
        """Padroniza nomes das colunas"""
        # Remove espaços extras e converte para minúsculas
        self.df.columns = self.df.columns.str.strip().str.upper()
        
        # Mapeamento de possíveis nomes de colunas
        mapeamento = {
            'NOME': 'NOME_FUNCIONARIO',
            'FUNCIONÁRIO': 'NOME_FUNCIONARIO',
            'FUNCIONARIO': 'NOME_FUNCIONARIO',
            'COLABORADOR': 'NOME_FUNCIONARIO',
            
            'SETOR': 'SETOR',
            'DEPARTAMENTO': 'SETOR',
            'ÁREA': 'SETOR',
            'AREA': 'SETOR',
            'DESCCENTROCUSTO2': 'SETOR',
            'DESCCENTROCUSTO3': 'SETOR',
            
            'CARGO': 'CARGO',
            'FUNÇÃO': 'CARGO',
            'FUNCAO': 'CARGO',
            
            'SEXO': 'GENERO',
            'GÊNERO': 'GENERO',
            'GENERO': 'GENERO',
            
            'DATA AFASTAMENTO': 'DATA_AFASTAMENTO',
            'DATA DE AFASTAMENTO': 'DATA_AFASTAMENTO',
            'DT AFASTAMENTO': 'DATA_AFASTAMENTO',
            
            'DATA RETORNO': 'DATA_RETORNO',
            'DATA DE RETORNO': 'DATA_RETORNO',
            'DT RETORNO': 'DATA_RETORNO',
            
            'TIPO DE ATESTADO': 'TIPO_ATESTADO',
            'TIPO ATESTADO': 'TIPO_ATESTADO',
            'TIPO': 'TIPO_ATESTADO',
            'TIPOINFOATEST': 'TIPO_INFO_ATESTADO',
            'DESCTIPOINFOATEST': 'TIPO_ATESTADO',
            
            'CID': 'CID',
            'CID10': 'CID',
            
            'DESCRIÇÃO CID': 'DESCRICAO_CID',
            'DESCRICAO CID': 'DESCRICAO_CID',
            'DESC CID': 'DESCRICAO_CID',
            'DESCCID': 'DESCRICAO_CID',
            
            'NRODIASATESTADO': 'NUMERO_DIAS_ATESTADO',
            'NRO DIAS ATESTADO': 'NUMERO_DIAS_ATESTADO',
            'DIAS ATESTADO': 'NUMERO_DIAS_ATESTADO',
            'QTD DIAS': 'NUMERO_DIAS_ATESTADO',
            
            'NROHORASATESTADO': 'NUMERO_HORAS_ATESTADO',
            'NRO HORAS ATESTADO': 'NUMERO_HORAS_ATESTADO',
            'HORAS ATESTADO': 'NUMERO_HORAS_ATESTADO',
            'QTD HORAS': 'NUMERO_HORAS_ATESTADO',
            
            'MÉDIA HORAS PERDIDAS': 'HORAS_PERDIDAS',
            'MEDIA HORAS PERDIDAS': 'HORAS_PERDIDAS',
            'HORAS PERDIDAS': 'HORAS_PERDIDAS',
            
            'CPF': 'CPF',
            'MATRÍCULA': 'MATRICULA',
            'MATRICULA': 'MATRICULA',
        }
        
        # Renomeia as colunas
        for col_atual in self.df.columns:
            if col_atual in mapeamento:
                self.df.rename(columns={col_atual: mapeamento[col_atual]}, inplace=True)
    
    def limpar_dados(self):
        """Limpa e valida os dados"""
        # Remove linhas completamente vazias
        self.df.dropna(how='all', inplace=True)
        
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
        
        self.padronizar_colunas()
        self.limpar_dados()
        self.calcular_metricas()
        
        # Converte para lista de dicionários
        registros = []
        for _, row in self.df.iterrows():
            registro = {
                'nome_funcionario': str(row.get('NOME_FUNCIONARIO', '')),
                'cpf': str(row.get('CPF', '')),
                'matricula': str(row.get('MATRICULA', '')),
                'setor': str(row.get('SETOR', '')),
                'cargo': str(row.get('CARGO', '')),
                'genero': str(row.get('GENERO', ''))[:1].upper() if pd.notna(row.get('GENERO')) else '',
                'data_afastamento': row.get('DATA_AFASTAMENTO'),
                'data_retorno': row.get('DATA_RETORNO'),
                'tipo_info_atestado': int(row.get('TIPO_INFO_ATESTADO', 0)) if pd.notna(row.get('TIPO_INFO_ATESTADO')) else None,
                'tipo_atestado': str(row.get('TIPO_ATESTADO', '')),
                'cid': str(row.get('CID', '')),
                'descricao_cid': str(row.get('DESCRICAO_CID', '')),
                'numero_dias_atestado': float(row.get('NUMERO_DIAS_ATESTADO', 0)),
                'numero_horas_atestado': float(row.get('NUMERO_HORAS_ATESTADO', 0)),
                'dias_perdidos': float(row.get('DIAS_PERDIDOS', 0)),
                'horas_perdidas': float(row.get('HORAS_PERDIDAS', 0)),
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
