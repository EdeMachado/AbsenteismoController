"""
Teste de PDF com imagem (gráfico matplotlib)
Para verificar se o problema está na adição de imagens ao PDF
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
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from datetime import datetime

def gerar_grafico_teste(output_path):
    """Gera um gráfico simples de teste"""
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Dados simples
        x = np.arange(5)
        y = [10, 20, 15, 25, 30]
        
        ax.bar(x, y, color='#1a237e')
        ax.set_xlabel('Categoria')
        ax.set_ylabel('Valor')
        ax.set_title('Gráfico de Teste')
        ax.set_xticks(x)
        ax.set_xticklabels(['A', 'B', 'C', 'D', 'E'])
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return True
    except Exception as e:
        print(f"❌ Erro ao gerar gráfico: {e}")
        return False

def testar_pdf_com_imagem():
    """Gera PDF com imagem (gráfico)"""
    try:
        exports_dir = "exports"
        os.makedirs(exports_dir, exist_ok=True)
        
        output_path = os.path.join(exports_dir, "teste_pdf_com_imagem.pdf")
        grafico_path = os.path.join(exports_dir, "teste_grafico.png")
        
        # Remove arquivos existentes
        for path in [output_path, grafico_path]:
            if os.path.exists(path):
                os.remove(path)
        
        print(f"🔍 Gerando gráfico de teste...")
        if not gerar_grafico_teste(grafico_path):
            return False
        
        if not os.path.exists(grafico_path):
            print("❌ Gráfico não foi gerado!")
            return False
        
        tamanho_grafico = os.path.getsize(grafico_path)
        print(f"✅ Gráfico gerado: {grafico_path} ({tamanho_grafico} bytes)")
        
        print(f"🔍 Gerando PDF com imagem: {output_path}")
        
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
        
        story.append(Paragraph("Teste de PDF com Imagem", title_style))
        story.append(Spacer(1, 20))
        
        # Texto
        story.append(Paragraph("Este PDF contém uma imagem (gráfico matplotlib).", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Adiciona imagem
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
            story.append(img)
            story.append(Spacer(1, 20))
            print("✅ Imagem adicionada ao PDF")
        except Exception as e:
            print(f"❌ Erro ao adicionar imagem: {e}")
            import traceback
            traceback.print_exc()
            return False
        
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
        
        print(f"✅ PDF com imagem gerado com sucesso!")
        print(f"   Arquivo: {output_path}")
        print(f"   Tamanho: {tamanho} bytes")
        print(f"   Header: {header[:8]}")
        print(f"\n📋 TESTE: Abra o arquivo no Adobe Acrobat Reader")
        print(f"   Se abrir corretamente, o problema está nos dados específicos")
        print(f"   Se não abrir, o problema está na adição de imagens ao PDF")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO ao gerar PDF com imagem: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("TESTE DE PDF COM IMAGEM - ISOLAMENTO DE PROBLEMA")
    print("=" * 60)
    print()
    
    sucesso = testar_pdf_com_imagem()
    
    print()
    print("=" * 60)
    if sucesso:
        print("✅ Teste concluído - Verifique o arquivo gerado")
    else:
        print("❌ Teste falhou - Verifique os erros acima")
    print("=" * 60)

