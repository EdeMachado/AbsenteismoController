"""
Módulo de Segurança - Validação e Sanitização
Proteção contra OWASP Top 10
"""
import re
import html
import os
from typing import Optional
from datetime import datetime
from fastapi import HTTPException, status


def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """
    Sanitiza strings para prevenir XSS e injection
    Remove caracteres perigosos e limita tamanho
    """
    if not isinstance(value, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valor deve ser uma string"
        )
    
    # Remove caracteres de controle e normaliza
    value = value.strip()
    
    # Remove caracteres perigosos para SQL/XSS
    dangerous_chars = ['<', '>', '"', "'", ';', '--', '/*', '*/', 'xp_', 'sp_']
    for char in dangerous_chars:
        if char in value.lower():
            # Escapa ao invés de remover para não perder dados legítimos
            value = value.replace(char, '')
    
    # Limita tamanho
    if max_length and len(value) > max_length:
        value = value[:max_length]
    
    return value


def validate_email(email: str) -> str:
    """Valida formato de email"""
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email é obrigatório"
        )
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email inválido"
        )
    
    return email.lower().strip()


def validate_client_id(client_id: Optional[int]) -> int:
    """Valida client_id para prevenir injection"""
    if client_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="client_id é obrigatório"
        )
    
    if not isinstance(client_id, int) or client_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="client_id inválido"
        )
    
    return client_id


def validate_filename(filename: str) -> str:
    """Valida nome de arquivo para prevenir path traversal"""
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome de arquivo é obrigatório"
        )
    
    # Remove path traversal
    filename = os.path.basename(filename)
    
    # Remove caracteres perigosos
    dangerous = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
    for char in dangerous:
        filename = filename.replace(char, '')
    
    # Limita tamanho
    if len(filename) > 255:
        filename = filename[:255]
    
    return filename


def sanitize_sql_input(value: str) -> str:
    """
    Sanitiza input para prevenir SQL injection
    Remove padrões perigosos de SQL
    """
    if not isinstance(value, str):
        return ""
    
    # Padrões perigosos de SQL
    sql_patterns = [
        r'(\bOR\b|\bAND\b)\s*[\'"]?\s*\d+\s*=\s*\d+',
        r'(\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b)',
        r'(\bEXEC\b|\bEXECUTE\b|\bEXEC\s*\()',
        r'(\bxp_\w+|\bsp_\w+)',
        r'--.*$',
        r'/\*.*?\*/',
        r';\s*(DROP|DELETE|UPDATE|INSERT)',
    ]
    
    for pattern in sql_patterns:
        value = re.sub(pattern, '', value, flags=re.IGNORECASE)
    
    return value.strip()


def validate_file_upload(filename: str, content_type: Optional[str], max_size: int = 10 * 1024 * 1024) -> tuple:
    """
    Valida upload de arquivo
    Retorna (filename_safe, is_valid)
    """
    # Valida extensão
    allowed_extensions = ['.xlsx', '.xls', '.csv', '.png', '.jpg', '.jpeg', '.gif', '.svg']
    ext = os.path.splitext(filename)[1].lower()
    
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de arquivo não permitido. Permitidos: {', '.join(allowed_extensions)}"
        )
    
    # Valida content type
    if content_type:
        allowed_types = [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel',
            'text/csv',
            'image/png',
            'image/jpeg',
            'image/gif',
            'image/svg+xml'
        ]
        if content_type not in allowed_types and not any(ct in content_type for ct in ['image/', 'text/csv']):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de conteúdo não permitido"
            )
    
    # Sanitiza filename
    safe_filename = validate_filename(filename)
    
    return safe_filename, True


def escape_html(text: str) -> str:
    """Escapa HTML para prevenir XSS"""
    if not isinstance(text, str):
        return ""
    return html.escape(text)


def validate_date_range(start_date: Optional[str], end_date: Optional[str]) -> tuple:
    """Valida intervalo de datas"""
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            if start > end:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Data início deve ser anterior à data fim"
                )
            return start_date, end_date
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de data inválido. Use YYYY-MM-DD"
            )
    return start_date, end_date

