"""
Teste de geração de PDF mínimo - sem gráficos
Para isolar o problema de corrupção do PDF
"""
import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from datetime import datetime

def testar_pdf_minimo():
    """Gera PDF mínimo apenas com texto e tabela - sem gráficos"""
    try:
        # Cria diretório de exports se não existir
        exports_dir = "exports"
        os.makedirs(exports_dir, exist_ok=True)
        
        # Caminho do arquivo
        output_path = os.path.join(exports_dir, "teste_pdf_minimo.pdf")
        
        # Remove arquivo existente
        if os.path.exists(output_path):
            os.remove(output_path)
        
        print(f"🔍 Gerando PDF mínimo de teste: {output_path}")
        
        # Cria documento
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        # Título
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        story.append(Paragraph("Teste de PDF Mínimo", title_style))
        story.append(Spacer(1, 20))
        
        # Texto simples
        story.append(Paragraph("Este é um teste de geração de PDF sem gráficos.", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Tabela simples
        data = [
            ['Item', 'Valor'],
            ['Teste 1', '100'],
            ['Teste 2', '200'],
            ['Teste 3', '300']
        ]
        
        table = Table(data, colWidths=[10*cm, 6*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 20))
        
        # Data
        story.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles['Normal']))
        
        # Gera PDF
        print("📄 Construindo PDF...")
        doc.build(story)
        
        # Valida
        if not os.path.exists(output_path):
            print("❌ ERRO: PDF não foi criado!")
            return False
        
        tamanho = os.path.getsize(output_path)
        if tamanho == 0:
            print("❌ ERRO: PDF está vazio!")
            return False
        
        # Valida header
        with open(output_path, 'rb') as f:
            header = f.read(8)
            if not header.startswith(b'%PDF'):
                print(f"❌ ERRO: PDF não tem header válido! Header: {header}")
                return False
        
        print(f"✅ PDF mínimo gerado com sucesso!")
        print(f"   Arquivo: {output_path}")
        print(f"   Tamanho: {tamanho} bytes")
        print(f"   Header: {header[:8]}")
        print(f"\n📋 TESTE: Abra o arquivo no Adobe Acrobat Reader")
        print(f"   Se abrir corretamente, o problema está nos gráficos ou dados")
        print(f"   Se não abrir, o problema está na estrutura básica do PDF")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO ao gerar PDF mínimo: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("TESTE DE PDF MÍNIMO - ISOLAMENTO DE PROBLEMA")
    print("=" * 60)
    print()
    
    sucesso = testar_pdf_minimo()
    
    print()
    print("=" * 60)
    if sucesso:
        print("✅ Teste concluído - Verifique o arquivo gerado")
    else:
        print("❌ Teste falhou - Verifique os erros acima")
    print("=" * 60)

