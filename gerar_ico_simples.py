#!/usr/bin/env python3
"""
Gera arquivo .ico simples a partir do SVG
Versão simplificada - cria ICO básico
"""

import os
import sys

def criar_ico_manual():
    """Cria um ICO básico usando apenas PIL"""
    
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("📦 Instalando Pillow...")
        os.system(f"{sys.executable} -m pip install Pillow -q")
        from PIL import Image, ImageDraw, ImageFont
    
    print("🎨 Gerando ícone .ico...")
    
    # Tamanhos para o ICO
    tamanhos = [16, 32, 48, 64, 128, 256]
    imagens = []
    
    for tamanho in tamanhos:
        # Cria imagem com fundo transparente
        img = Image.new('RGBA', (tamanho, tamanho), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Cores do gradiente (azul)
        cor_escura = (26, 35, 126)  # #1a237e
        cor_clara = (57, 73, 171)   # #3949ab
        
        # Desenha fundo com gradiente simples
        for y in range(tamanho):
            # Calcula cor baseada na posição (gradiente vertical)
            ratio = y / tamanho
            r = int(cor_escura[0] * (1 - ratio) + cor_clara[0] * ratio)
            g = int(cor_escura[1] * (1 - ratio) + cor_clara[1] * ratio)
            b = int(cor_escura[2] * (1 - ratio) + cor_clara[2] * ratio)
            draw.line([(0, y), (tamanho, y)], fill=(r, g, b, 255))
        
        # Desenha bordas arredondadas (simulado)
        # Desenha a letra "A"
        # Calcula proporções
        margem = tamanho * 0.15
        largura_letra = tamanho * 0.4
        altura_letra = tamanho * 0.5
        
        x_centro = tamanho / 2
        y_inicio = tamanho * 0.25
        y_fim = tamanho * 0.75
        
        # Desenha "A" simplificado
        # Lado esquerdo
        draw.line([
            (x_centro - largura_letra/2, y_fim),
            (x_centro, y_inicio)
        ], fill=(255, 255, 255, 255), width=max(2, tamanho//20))
        
        # Lado direito
        draw.line([
            (x_centro, y_inicio),
            (x_centro + largura_letra/2, y_fim)
        ], fill=(255, 255, 255, 255), width=max(2, tamanho//20))
        
        # Trave horizontal
        y_trave = y_inicio + altura_letra * 0.4
        draw.line([
            (x_centro - largura_letra/3, y_trave),
            (x_centro + largura_letra/3, y_trave)
        ], fill=(255, 255, 255, 255), width=max(2, tamanho//20))
        
        # Linha decorativa inferior
        y_linha = tamanho * 0.85
        draw.rectangle([
            (tamanho * 0.2, y_linha),
            (tamanho * 0.8, y_linha + max(2, tamanho//30))
        ], fill=(255, 255, 255, 200))
        
        imagens.append(img)
        print(f"  ✅ {tamanho}x{tamanho}px")
    
    # Salva como ICO
    ico_path = "frontend/static/favicon.ico"
    os.makedirs(os.path.dirname(ico_path), exist_ok=True)
    
    imagens[0].save(
        ico_path,
        format='ICO',
        sizes=[(img.width, img.height) for img in imagens]
    )
    
    print(f"\n✅ Ícone criado: {ico_path}")
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("🎨 GERADOR DE ÍCONE .ICO (Versão Simples)")
    print("=" * 50)
    print()
    
    if criar_ico_manual():
        print()
        print("=" * 50)
        print("✅ PRONTO!")
        print("=" * 50)
        print()
        print("📁 Arquivo: frontend/static/favicon.ico")
        print()
        print("💡 Para usar no atalho:")
        print("   1. Clique direito no atalho > Propriedades")
        print("   2. Alterar Ícone...")
        print("   3. Selecione: frontend\\static\\favicon.ico")
    else:
        print("❌ Erro ao gerar ícone")
        sys.exit(1)



