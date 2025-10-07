#!/usr/bin/env python3
"""
Script para reprocessar dados existentes com correções de encoding
"""
import os
import sys
sys.path.append(os.path.dirname(__file__))

from backend.database import get_db
from backend.models import Atestado, Upload
from backend.excel_processor import ExcelProcessor
import pandas as pd

def reprocessar_dados():
    """Reprocessa dados existentes"""
    db = next(get_db())
    
    try:
        # Busca todos os uploads
        uploads = db.query(Upload).all()
        
        for upload in uploads:
            print(f"Reprocessando upload {upload.id}: {upload.filename}")
            
            # Busca atestados do upload
            atestados = db.query(Atestado).filter(Atestado.upload_id == upload.id).all()
            
            for atestado in atestados:
                # Corrige encoding dos campos de texto
                if atestado.descricao_cid:
                    atestado.descricao_cid = corrigir_encoding(atestado.descricao_cid)
                
                if atestado.setor:
                    atestado.setor = corrigir_encoding(atestado.setor)
                
                if atestado.nome_funcionario:
                    atestado.nome_funcionario = corrigir_encoding(atestado.nome_funcionario)
        
        db.commit()
        print("Dados reprocessados com sucesso!")
        
    except Exception as e:
        print(f"Erro ao reprocessar: {e}")
        db.rollback()
    finally:
        db.close()

def corrigir_encoding(texto):
    """Corrige encoding de caracteres especiais"""
    if not texto:
        return texto
    
    # Mapeamento de caracteres mal codificados
    correcoes = {
        '??': 'ã', '??': 'é', '??': 'í', '??': 'ó', '??': 'ú', '??': 'ç',
        '??': 'á', '??': 'ê', '??': 'ô', '??': 'õ', '??': 'à', '??': 'è',
        '??': 'ì', '??': 'ò', '??': 'ù', '??': 'ñ', '??': 'ü', '??': 'ä',
        '??': 'ö', '??': 'ß', '??': 'Ä', '??': 'Ö', '??': 'Ü'
    }
    
    texto_corrigido = str(texto)
    for mal_codificado, correto in correcoes.items():
        texto_corrigido = texto_corrigido.replace(mal_codificado, correto)
    
    return texto_corrigido

if __name__ == "__main__":
    reprocessar_dados()
