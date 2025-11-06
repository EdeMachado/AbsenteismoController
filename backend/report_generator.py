"""
Gerador de relatórios em PDF e Excel
"""
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import pandas as pd
from typing import List, Dict, Any, Optional
import os
import io
import matplotlib
matplotlib.use('Agg')  # Backend sem interface gráfica
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import font_manager
import numpy as np

class ReportGenerator:
    """Gerador de relatórios"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configura estilos customizados"""
        # Título principal
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # Subtítulo
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#283593'),
            spaceAfter=20,
            alignment=TA_CENTER
        )
        
        # Cabeçalho de seção
        self.section_style = ParagraphStyle(
            'CustomSection',
            parent=self.styles['Heading2'],
            fontSize=18,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=15,
            spaceBefore=20,
            fontName='Helvetica-Bold'
        )
        
        # Texto normal
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#212121'),
            spaceAfter=12
        )
    
    def _gerar_grafico_cids(self, top_cids: List[Dict], output_path: str) -> Optional[str]:
        """Gera gráfico de barras horizontal para TOP CIDs"""
        try:
            if not top_cids or len(top_cids) == 0:
                return None
            
            fig, ax = plt.subplots(figsize=(10, 6))
            top10 = top_cids[:10]
            
            cids = [f"{c.get('cid', 'N/A')}" for c in top10]
            quantidades = [c.get('quantidade', 0) for c in top10]
            
            colors_list = ['#1a237e' if i % 2 == 0 else '#556B2F' for i in range(len(cids))]
            bars = ax.barh(range(len(cids)), quantidades, color=colors_list)
            
            ax.set_yticks(range(len(cids)))
            ax.set_yticklabels(cids, fontsize=9)
            ax.set_xlabel('Quantidade de Atestados', fontsize=10, fontweight='bold')
            ax.set_title('TOP 10 Doenças Mais Frequentes', fontsize=12, fontweight='bold', pad=15)
            ax.grid(axis='x', alpha=0.3)
            
            # Adiciona valores nas barras
            for i, (bar, qtd) in enumerate(zip(bars, quantidades)):
                ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2, 
                       str(qtd), va='center', fontsize=9)
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            return output_path
        except Exception as e:
            print(f"Erro ao gerar gráfico CIDs: {e}")
            return None
    
    def _gerar_grafico_funcionarios(self, top_func: List[Dict], output_path: str) -> Optional[str]:
        """Gera gráfico de barras para TOP Funcionários"""
        try:
            if not top_func or len(top_func) == 0:
                return None
            
            fig, ax = plt.subplots(figsize=(10, 6))
            top10 = top_func[:10]
            
            nomes = [f.get('nome', 'N/A')[:20] for f in top10]
            dias = [f.get('dias_perdidos', 0) for f in top10]
            
            colors_list = ['#1a237e' if i % 2 == 0 else '#556B2F' for i in range(len(nomes))]
            bars = ax.bar(range(len(nomes)), dias, color=colors_list)
            
            ax.set_xticks(range(len(nomes)))
            ax.set_xticklabels(nomes, rotation=45, ha='right', fontsize=9)
            ax.set_ylabel('Dias Perdidos', fontsize=10, fontweight='bold')
            ax.set_title('TOP 10 Funcionários com Mais Dias Perdidos', fontsize=12, fontweight='bold', pad=15)
            ax.grid(axis='y', alpha=0.3)
            
            # Adiciona valores nas barras
            for bar, dia in zip(bars, dias):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                       str(int(dia)), ha='center', va='bottom', fontsize=9)
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            return output_path
        except Exception as e:
            print(f"Erro ao gerar gráfico funcionários: {e}")
            return None
    
    def _gerar_grafico_setores(self, top_setores: List[Dict], output_path: str) -> Optional[str]:
        """Gera gráfico de barras para TOP Setores"""
        try:
            if not top_setores or len(top_setores) == 0:
                return None
            
            fig, ax = plt.subplots(figsize=(10, 6))
            top10 = top_setores[:10]
            
            setores = [s.get('setor', 'N/A')[:20] for s in top10]
            dias = [s.get('dias_perdidos', 0) for s in top10]
            
            colors_list = ['#1a237e' if i % 2 == 0 else '#556B2F' for i in range(len(setores))]
            bars = ax.bar(range(len(setores)), dias, color=colors_list)
            
            ax.set_xticks(range(len(setores)))
            ax.set_xticklabels(setores, rotation=45, ha='right', fontsize=9)
            ax.set_ylabel('Dias Perdidos', fontsize=10, fontweight='bold')
            ax.set_title('TOP 10 Setores com Mais Dias Perdidos', fontsize=12, fontweight='bold', pad=15)
            ax.grid(axis='y', alpha=0.3)
            
            # Adiciona valores nas barras
            for bar, dia in zip(bars, dias):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                       str(int(dia)), ha='center', va='bottom', fontsize=9)
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            return output_path
        except Exception as e:
            print(f"Erro ao gerar gráfico setores: {e}")
            return None
    
    def _gerar_grafico_evolucao(self, evolucao: List[Dict], output_path: str) -> Optional[str]:
        """Gera gráfico de linha para evolução mensal"""
        try:
            if not evolucao or len(evolucao) == 0:
                return None
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            meses = [e.get('mes', 'N/A')[-5:] if len(e.get('mes', '')) >= 5 else e.get('mes', 'N/A') for e in evolucao]
            dias = [e.get('dias_perdidos', 0) for e in evolucao]
            
            ax.plot(range(len(meses)), dias, marker='o', linewidth=2, markersize=6, 
                   color='#1a237e', label='Dias Perdidos')
            ax.fill_between(range(len(meses)), dias, alpha=0.3, color='#1a237e')
            
            ax.set_xticks(range(len(meses)))
            ax.set_xticklabels(meses, rotation=45, ha='right', fontsize=9)
            ax.set_ylabel('Dias Perdidos', fontsize=10, fontweight='bold')
            ax.set_title('Evolução Mensal de Dias Perdidos', fontsize=12, fontweight='bold', pad=15)
            ax.grid(True, alpha=0.3)
            ax.legend()
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            return output_path
        except Exception as e:
            print(f"Erro ao gerar gráfico evolução: {e}")
            return None
    
    def generate_pdf_report(self, 
                           output_path: str,
                           dados: Dict[str, Any],
                           metricas: Dict[str, Any],
                           insights: Optional[List[Dict[str, Any]]] = None,
                           periodo: Optional[str] = None) -> bool:
        """Gera relatório PDF completo"""
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            story = []
            
            # Cabeçalho
            story.append(Paragraph("Relatório de Absenteísmo", self.title_style))
            story.append(Paragraph("AbsenteismoController - GrupoBiomed", self.subtitle_style))
            
            if periodo:
                story.append(Paragraph(f"Período: {periodo}", self.normal_style))
            
            story.append(Paragraph(f"Data de geração: {datetime.now().strftime('%d/%m/%Y %H:%M')}", self.normal_style))
            story.append(Spacer(1, 20))
            
            # Métricas principais
            story.append(Paragraph("Indicadores Principais", self.section_style))
            
            metrics_data = [
                ['Métrica', 'Valor'],
                ['Total de Atestados', f"{int(metricas.get('total_atestados', 0))}"],
                ['Dias Perdidos', f"{int(metricas.get('total_dias_perdidos', 0))}"],
                ['Horas Perdidas', f"{int(metricas.get('total_horas_perdidas', 0))}"],
                ['Atestados (Dias)', f"{int(metricas.get('total_atestados_dias', 0))}"],
            ]
            
            metrics_table = Table(metrics_data, colWidths=[10*cm, 6*cm])
            metrics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            
            story.append(metrics_table)
            story.append(Spacer(1, 30))
            
            # Gera gráficos temporários
            temp_dir = os.path.dirname(output_path)
            timestamp_unique = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            graficos_temp = []
            
            # Gráfico de Evolução Mensal
            if 'evolucao_mensal' in dados and dados['evolucao_mensal']:
                evolucao_path = os.path.join(temp_dir, f"evolucao_{timestamp_unique}.png")
                if self._gerar_grafico_evolucao(dados['evolucao_mensal'], evolucao_path):
                    graficos_temp.append(evolucao_path)
                    story.append(Paragraph("Evolução Mensal de Dias Perdidos", self.section_style))
                    story.append(Image(evolucao_path, width=16*cm, height=8*cm))
                    story.append(Spacer(1, 20))
            
            # Gráfico TOP CIDs
            if 'top_cids' in dados and dados['top_cids']:
                cids_path = os.path.join(temp_dir, f"cids_{timestamp_unique}.png")
                if self._gerar_grafico_cids(dados['top_cids'], cids_path):
                    graficos_temp.append(cids_path)
                    story.append(Paragraph("TOP 10 Doenças Mais Frequentes", self.section_style))
                    story.append(Image(cids_path, width=16*cm, height=8*cm))
                    story.append(Spacer(1, 20))
            
            # Gráfico TOP Funcionários
            if 'top_funcionarios' in dados and dados['top_funcionarios']:
                func_path = os.path.join(temp_dir, f"funcionarios_{timestamp_unique}.png")
                if self._gerar_grafico_funcionarios(dados['top_funcionarios'], func_path):
                    graficos_temp.append(func_path)
                    story.append(Paragraph("TOP 10 Funcionários com Mais Dias Perdidos", self.section_style))
                    story.append(Image(func_path, width=16*cm, height=8*cm))
                    story.append(Spacer(1, 20))
            
            # Gráfico TOP Setores
            if 'top_setores' in dados and dados['top_setores']:
                setor_path = os.path.join(temp_dir, f"setores_{timestamp_unique}.png")
                if self._gerar_grafico_setores(dados['top_setores'], setor_path):
                    graficos_temp.append(setor_path)
                    story.append(Paragraph("TOP 10 Setores com Mais Dias Perdidos", self.section_style))
                    story.append(Image(setor_path, width=16*cm, height=8*cm))
                    story.append(Spacer(1, 20))
            
            story.append(PageBreak())
            
            # Insights e Análises
            if insights and len(insights) > 0:
                story.append(Paragraph("Análises e Insights Automáticos", self.section_style))
                story.append(Spacer(1, 15))
                
                for insight in insights:
                    # Título do insight
                    story.append(Paragraph(f"<b>{insight.get('icone', '📊')} {insight.get('titulo', 'Insight')}</b>", 
                                         ParagraphStyle('InsightTitle', parent=self.normal_style, fontSize=13, textColor=colors.HexColor('#1a237e'), spaceAfter=8)))
                    
                    # Descrição
                    story.append(Paragraph(insight.get('descricao', ''), self.normal_style))
                    
                    # Recomendação
                    if insight.get('recomendacao'):
                        story.append(Paragraph(f"<b>💡 Recomendação:</b> {insight.get('recomendacao')}", 
                                             ParagraphStyle('Recomendacao', parent=self.normal_style, fontSize=10, 
                                                          leftIndent=20, textColor=colors.HexColor('#556B2F'), spaceAfter=15)))
                    
                    story.append(Spacer(1, 10))
            
            story.append(PageBreak())
            
            # TOP 10 CIDs (Tabela)
            if 'top_cids' in dados and dados['top_cids']:
                story.append(Paragraph("TOP 10 Doenças Mais Frequentes", self.section_style))
                
                cids_data = [['CID', 'Diagnóstico', 'Quantidade', 'Dias Perdidos']]
                for cid in dados['top_cids'][:10]:
                    cids_data.append([
                        cid.get('cid', 'N/A'),
                        cid.get('descricao', cid.get('diagnostico', 'N/A'))[:50],
                        str(cid.get('quantidade', 0)),
                        str(int(cid.get('dias_perdidos', 0)))
                    ])
                
                cids_table = Table(cids_data, colWidths=[3*cm, 7*cm, 3*cm, 3*cm])
                cids_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                ]))
                
                story.append(cids_table)
                story.append(Spacer(1, 30))
            
            # TOP Funcionários
            if 'top_funcionarios' in dados and dados['top_funcionarios']:
                story.append(Paragraph("TOP 10 Funcionários com Mais Dias Perdidos", self.section_style))
                
                func_data = [['Funcionário', 'Setor', 'Dias Perdidos', 'Atestados']]
                for func in dados['top_funcionarios'][:10]:
                    func_data.append([
                        func.get('nome', 'N/A')[:40],
                        func.get('setor', 'N/A')[:30],
                        str(int(func.get('dias_perdidos', 0))),
                        str(func.get('quantidade_atestados', 0))
                    ])
                
                func_table = Table(func_data, colWidths=[5*cm, 4*cm, 3*cm, 3*cm])
                func_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                ]))
                
                story.append(func_table)
                story.append(Spacer(1, 30))
            
            # TOP Setores
            if 'top_setores' in dados and dados['top_setores']:
                story.append(Paragraph("TOP 10 Setores com Mais Atestados", self.section_style))
                
                setor_data = [['Setor', 'Dias Perdidos', 'Atestados']]
                for setor in dados['top_setores'][:10]:
                    setor_data.append([
                        setor.get('setor', 'N/A')[:40],
                        str(int(setor.get('dias_perdidos', 0))),
                        str(setor.get('quantidade', 0))
                    ])
                
                setor_table = Table(setor_data, colWidths=[8*cm, 4*cm, 4*cm])
                setor_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                ]))
                
                story.append(setor_table)
                story.append(Spacer(1, 30))
            
            # Rodapé
            story.append(Spacer(1, 20))
            story.append(Paragraph(
                f"<i>Relatório gerado automaticamente pelo AbsenteismoController v2.0</i>",
                self.normal_style
            ))
            
            # Build PDF
            doc.build(story)
            
            # Remove arquivos temporários de gráficos
            for temp_file in graficos_temp:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except:
                    pass
            
            return True
            
        except Exception as e:
            print(f"Erro ao gerar PDF: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def generate_excel_report(self,
                             output_path: str,
                             dados: List[Dict[str, Any]],
                             metricas: Dict[str, Any],
                             periodo: Optional[str] = None) -> bool:
        """Gera relatório Excel completo"""
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Aba 1: Dados Completos
                if dados:
                    df_dados = pd.DataFrame(dados)
                    df_dados.to_excel(writer, sheet_name='Dados Completos', index=False)
                
                # Aba 2: Métricas
                df_metricas = pd.DataFrame([
                    {'Métrica': 'Total de Atestados', 'Valor': metricas.get('total_atestados', 0)},
                    {'Métrica': 'Dias Perdidos', 'Valor': metricas.get('total_dias_perdidos', 0)},
                    {'Métrica': 'Horas Perdidas', 'Valor': metricas.get('total_horas_perdidas', 0)},
                    {'Métrica': 'Atestados (Dias)', 'Valor': metricas.get('total_atestados_dias', 0)},
                ])
                df_metricas.to_excel(writer, sheet_name='Métricas', index=False)
                
                # Aba 3: TOP CIDs
                if 'top_cids' in metricas and metricas['top_cids']:
                    df_cids = pd.DataFrame(metricas['top_cids'])
                    df_cids.to_excel(writer, sheet_name='TOP CIDs', index=False)
                
                # Aba 4: TOP Funcionários
                if 'top_funcionarios' in metricas and metricas['top_funcionarios']:
                    df_func = pd.DataFrame(metricas['top_funcionarios'])
                    df_func.to_excel(writer, sheet_name='TOP Funcionários', index=False)
                
                # Aba 5: TOP Setores
                if 'top_setores' in metricas and metricas['top_setores']:
                    df_setores = pd.DataFrame(metricas['top_setores'])
                    df_setores.to_excel(writer, sheet_name='TOP Setores', index=False)
            
            return True
            
        except Exception as e:
            print(f"Erro ao gerar Excel: {e}")
            import traceback
            traceback.print_exc()
            return False

