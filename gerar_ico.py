#!/usr/bin/env python3
"""
Script para gerar arquivo .ico a partir do SVG do logo
Requer: Pillow, cairosvg (ou podemos usar uma abordagem mais simples)
"""

import os
import sys

try:
    from PIL import Image
    import cairosvg
except ImportError:
    print("📦 Instalando dependências necessárias...")
    os.system(f"{sys.executable} -m pip install Pillow cairosvg -q")
    from PIL import Image
    import cairosvg

def gerar_ico():
    """Gera arquivo .ico a partir do SVG"""
    
    # Caminho do SVG
    svg_path = "frontend/static/logo-simples.svg"
    
    if not os.path.exists(svg_path):
        print(f"❌ Arquivo não encontrado: {svg_path}")
        return False
    
    # Tamanhos padrão para ICO
    tamanhos = [16, 32, 48, 64, 128, 256]
    
    print("🔄 Gerando ícone .ico...")
    
    # Lista para armazenar as imagens
    imagens = []
    
    # Converte SVG para PNG em cada tamanho
    for tamanho in tamanhos:
        try:
            # Converte SVG para PNG
            png_data = cairosvg.svg2png(
                url=svg_path,
                output_width=tamanho,
                output_height=tamanho
            )
            
            # Cria imagem PIL
            from io import BytesIO
            img = Image.open(BytesIO(png_data))
            
            # Converte para RGBA se necessário
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            imagens.append(img)
            print(f"  ✅ Tamanho {tamanho}x{tamanho}px gerado")
            
        except Exception as e:
            print(f"  ⚠️  Erro ao gerar {tamanho}x{tamanho}: {e}")
            continue
    
    if not imagens:
        print("❌ Nenhuma imagem foi gerada!")
        return False
    
    # Salva como ICO
    ico_path = "frontend/static/favicon.ico"
    imagens[0].save(
        ico_path,
        format='ICO',
        sizes=[(img.width, img.height) for img in imagens]
    )
    
    print(f"\n✅ Ícone criado com sucesso!")
    print(f"📁 Localização: {ico_path}")
    print(f"📏 Tamanhos incluídos: {', '.join([f'{img.width}x{img.height}' for img in imagens])}")
    
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("🎨 GERADOR DE ÍCONE .ICO")
    print("=" * 50)
    print()
    
    if gerar_ico():
        print()
        print("=" * 50)
        print("✅ PRONTO! Agora você pode usar o favicon.ico")
        print("=" * 50)
        print()
        print("💡 Para criar atalho no desktop:")
        print("   1. Clique com botão direito no atalho")
        print("   2. Propriedades > Alterar Ícone")
        print("   3. Selecione: frontend/static/favicon.ico")
    else:
        print()
        print("❌ Erro ao gerar ícone. Verifique as dependências.")
        sys.exit(1)



