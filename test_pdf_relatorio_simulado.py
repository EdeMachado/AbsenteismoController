"""
Teste de PDF simulando relatório real - com dados simples
Para verificar se o problema está na estrutura do relatório completo
"""
import os
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from datetime import datetime
import tempfile
import shutil

def sanitize_text(text):
    """Sanitiza texto - mesma função do report_generator"""
    if not text:
        return ""
    text = str(text)
    import re
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    return text

def gerar_grafico_simulado(output_path):
    """Gera gráfico simulado"""
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        x = np.arange(5)
        y = [10, 20, 15, 25, 30]
        ax.bar(x, y, color='#1a237e')
        ax.set_xlabel('Categoria')
        ax.set_ylabel('Valor')
        ax.set_title('Gráfico Simulado')
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        return True
    except Exception as e:
        print(f"❌ Erro ao gerar gráfico: {e}")
        return False

def testar_pdf_relatorio_simulado():
    """Gera PDF simulando estrutura do relatório real"""
    try:
        exports_dir = "exports"
        os.makedirs(exports_dir, exist_ok=True)
        
        output_path = os.path.join(exports_dir, "teste_pdf_relatorio_simulado.pdf")
        temp_output = output_path + '.tmp'
        
        # Remove arquivos existentes
        for path in [output_path, temp_output]:
            if os.path.exists(path):
                os.remove(path)
        
        print(f"🔍 Gerando PDF simulando relatório real...")
        
        # Gera gráfico temporário
        grafico_path = os.path.join(exports_dir, "teste_grafico_simulado.png")
        if not gerar_grafico_simulado(grafico_path):
            return False
        
        # Cria documento (usando temp como no código real)
        doc = SimpleDocTemplate(
            temp_output,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        # Estilos customizados (como no código real)
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        section_style = ParagraphStyle(
            'CustomSection',
            parent=styles['Heading2'],
            fontSize=18,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=15,
            spaceBefore=20,
            fontName='Helvetica-Bold'
        )
        
        # Cabeçalho (sanitizado)
        story.append(Paragraph(sanitize_text("Relatório de Absenteísmo"), title_style))
        story.append(Paragraph(sanitize_text("AbsenteismoController - GrupoBiomed"), styles['Normal']))
        story.append(Paragraph(sanitize_text(f"Data de geração: {datetime.now().strftime('%d/%m/%Y %H:%M')}"), styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Métricas (tabela)
        story.append(Paragraph(sanitize_text("Indicadores Principais"), section_style))
        metrics_data = [
            ['Métrica', 'Valor'],
            ['Total de Atestados', '100'],
            ['Dias Perdidos', '500'],
            ['Horas Perdidas', '1000'],
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
        ]))
        story.append(metrics_table)
        story.append(Spacer(1, 30))
        story.append(PageBreak())
        
        # Gráfico com KeepTogether (como no código real)
        conteudo_grafico = []
        conteudo_grafico.append(Paragraph(sanitize_text("Gráfico de Teste"), section_style))
        conteudo_grafico.append(Spacer(1, 10))
        
        # Adiciona imagem (mesma lógica do código real)
        try:
            # Valida imagem
            with open(grafico_path, 'rb') as f:
                header = f.read(8)
                if not (header.startswith(b'\x89PNG\r\n\x1a\n') or header.startswith(b'\xff\xd8\xff')):
                    print(f"⚠️ Arquivo não é PNG/JPG válido")
                    return False
            
            # Calcula aspect ratio
            try:
                from PIL import Image as PILImage
                with PILImage.open(grafico_path) as pil_img:
                    img_width, img_height = pil_img.size
                    aspect_ratio = img_width / img_height if img_height > 0 else 1.0
            except:
                aspect_ratio = 2.0
            
            width_pdf = 16*cm
            height_pdf = width_pdf / aspect_ratio if aspect_ratio > 0 else 8*cm
            if height_pdf > 10*cm:
                height_pdf = 10*cm
                width_pdf = height_pdf * aspect_ratio
            
            img = Image(grafico_path, width=width_pdf, height=height_pdf)
            conteudo_grafico.append(img)
            conteudo_grafico.append(Spacer(1, 15))
        except Exception as e:
            print(f"❌ Erro ao adicionar imagem: {e}")
            return False
        
        # Adiciona com KeepTogether (como no código real)
        try:
            if len(conteudo_grafico) <= 10:
                story.append(KeepTogether(conteudo_grafico))
            else:
                for item in conteudo_grafico:
                    story.append(item)
        except Exception as e:
            print(f"⚠️ Erro ao usar KeepTogether: {e}")
            for item in conteudo_grafico:
                story.append(item)
        
        story.append(Spacer(1, 20))
        story.append(PageBreak())
        
        # Tabela de dados (como no código real)
        story.append(Paragraph(sanitize_text("TOP 10 Doenças Mais Frequentes"), section_style))
        cids_data = [['CID', 'Diagnóstico', 'Quantidade', 'Dias Perdidos']]
        for i in range(5):
            cids_data.append([
                sanitize_text(f'CID{i+1}'),
                sanitize_text(f'Doença {i+1}'),
                str(i*10),
                str(i*5)
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
        ]))
        story.append(cids_table)
        
        # Rodapé
        story.append(Spacer(1, 20))
        story.append(Paragraph(
            sanitize_text("<i>Relatório gerado automaticamente pelo AbsenteismoController v2.0</i>"),
            styles['Normal']
        ))
        
        # Gera PDF (mesma lógica do código real)
        print("📄 Construindo PDF...")
        doc.build(story)
        
        # Fecha explicitamente
        del doc
        
        # Aguarda escrita
        import time
        time.sleep(0.3)
        
        # Valida temporário
        if not os.path.exists(temp_output):
            print("❌ ERRO: PDF temporário não foi criado!")
            return False
        
        tamanho_temp = os.path.getsize(temp_output)
        if tamanho_temp == 0:
            print("❌ ERRO: PDF temporário está vazio!")
            return False
        
        # Valida header temporário
        with open(temp_output, 'rb') as f:
            header = f.read(4)
            if header != b'%PDF':
                print(f"❌ ERRO: Arquivo temporário não é PDF válido!")
                return False
        
        # Move para destino final
        shutil.move(temp_output, output_path)
        
        # Valida final
        if not os.path.exists(output_path):
            print("❌ ERRO: PDF não foi movido para destino final!")
            return False
        
        tamanho = os.path.getsize(output_path)
        if tamanho == 0:
            print("❌ ERRO: PDF final está vazio!")
            return False
        
        # Valida header final
        with open(output_path, 'rb') as f:
            header = f.read(8)
            if not header.startswith(b'%PDF'):
                print(f"❌ ERRO: PDF final não tem header válido!")
                return False
        
        print(f"✅ PDF relatório simulado gerado com sucesso!")
        print(f"   Arquivo: {output_path}")
        print(f"   Tamanho: {tamanho} bytes")
        print(f"   Header: {header[:8]}")
        print(f"\n📋 TESTE: Abra o arquivo no Adobe Acrobat Reader")
        print(f"   Este PDF simula a estrutura completa do relatório real")
        print(f"   Se abrir corretamente, o problema está nos dados específicos da Roda de Ouro")
        
        # Remove gráfico temporário
        if os.path.exists(grafico_path):
            os.remove(grafico_path)
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO ao gerar PDF relatório simulado: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("TESTE DE PDF RELATÓRIO SIMULADO - ESTRUTURA COMPLETA")
    print("=" * 60)
    print()
    
    sucesso = testar_pdf_relatorio_simulado()
    
    print()
    print("=" * 60)
    if sucesso:
        print("✅ Teste concluído - Verifique o arquivo gerado")
    else:
        print("❌ Teste falhou - Verifique os erros acima")
    print("=" * 60)

