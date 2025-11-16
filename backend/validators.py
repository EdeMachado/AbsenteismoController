"""
Validadores Avançados de Dados
Validação de integridade referencial e regras de negócio
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import Optional, List
from .models import Client, Upload, Atestado
from .logger import app_logger


def validate_client_data_integrity(db: Session, client_id: int) -> dict:
    """
    Valida integridade dos dados de um cliente
    
    Verifica:
    - Uploads órfãos
    - Atestados sem upload
    - Referências quebradas
    
    Returns:
        Dict com resultados da validação
    """
    issues = []
    
    try:
        # Verifica se cliente existe
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        # Verifica uploads órfãos (sem atestados)
        uploads_sem_atestados = db.query(Upload).filter(
            Upload.client_id == client_id,
            ~Upload.id.in_(
                db.query(Atestado.upload_id).filter(Atestado.upload_id.isnot(None))
            )
        ).count()
        
        if uploads_sem_atestados > 0:
            issues.append({
                'type': 'warning',
                'message': f'{uploads_sem_atestados} upload(s) sem atestados associados',
                'severity': 'low'
            })
        
        # Verifica atestados órfãos (upload_id não existe)
        atestados_orfãos = db.query(Atestado).join(Upload).filter(
            Upload.client_id == client_id
        ).filter(
            ~Atestado.upload_id.in_(db.query(Upload.id).filter(Upload.client_id == client_id))
        ).count()
        
        if atestados_orfãos > 0:
            issues.append({
                'type': 'error',
                'message': f'{atestados_orfãos} atestado(s) com upload_id inválido',
                'severity': 'high'
            })
        
        # Conta total de registros
        total_uploads = db.query(Upload).filter(Upload.client_id == client_id).count()
        total_atestados = db.query(Atestado).join(Upload).filter(
            Upload.client_id == client_id
        ).count()
        
        return {
            'client_id': client_id,
            'valid': len([i for i in issues if i['severity'] == 'high']) == 0,
            'issues': issues,
            'stats': {
                'total_uploads': total_uploads,
                'total_atestados': total_atestados,
                'uploads_sem_atestados': uploads_sem_atestados,
                'atestados_orfãos': atestados_orfãos
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Erro ao validar integridade de dados do cliente {client_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao validar integridade de dados")


def validate_business_rules(db: Session, client_id: int, atestado_data: dict) -> List[str]:
    """
    Valida regras de negócio para atestados
    
    Args:
        db: Sessão do banco
        client_id: ID do cliente
        atestado_data: Dados do atestado a validar
    
    Returns:
        Lista de erros encontrados (vazia se válido)
    """
    errors = []
    
    # Valida datas
    if 'data_afastamento' in atestado_data and 'data_retorno' in atestado_data:
        if atestado_data['data_afastamento'] and atestado_data['data_retorno']:
            if atestado_data['data_retorno'] < atestado_data['data_afastamento']:
                errors.append("Data de retorno não pode ser anterior à data de afastamento")
    
    # Valida dias atestados
    if 'dias_atestados' in atestado_data:
        dias = atestado_data['dias_atestados']
        if dias is not None:
            if dias < 0:
                errors.append("Dias atestados não pode ser negativo")
            if dias > 365:
                errors.append("Dias atestados não pode ser maior que 365 dias")
    
    # Valida horas perdidas
    if 'horas_perdi' in atestado_data:
        horas = atestado_data['horas_perdi']
        if horas is not None:
            if horas < 0:
                errors.append("Horas perdidas não pode ser negativo")
            if horas > 8760:  # 365 dias * 24 horas
                errors.append("Horas perdidas excede limite razoável")
    
    return errors

