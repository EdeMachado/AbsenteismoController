"""
Handler de Upload com Timeout e Processamento Assíncrono
Suporta uploads grandes com timeout configurável e processamento em background
"""
import os
import asyncio
import time
from typing import Optional, Callable, Any
from fastapi import UploadFile, HTTPException
from .logger import app_logger, error_logger, log_operation

# Configurações
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
UPLOAD_TIMEOUT = 300  # 5 minutos
CHUNK_SIZE = 8192  # 8KB por chunk


async def save_upload_with_timeout(
    file: UploadFile,
    save_path: str,
    max_size: int = MAX_FILE_SIZE,
    timeout: int = UPLOAD_TIMEOUT,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> dict:
    """
    Salva arquivo de upload com timeout e validação de tamanho
    
    Args:
        file: Arquivo FastAPI UploadFile
        save_path: Caminho onde salvar o arquivo
        max_size: Tamanho máximo permitido em bytes
        timeout: Timeout em segundos
        progress_callback: Função callback para progresso (bytes_read, total_bytes)
    
    Returns:
        Dict com informações do arquivo salvo
    
    Raises:
        HTTPException: Se timeout ou tamanho excedido
    """
    start_time = time.time()
    bytes_read = 0
    
    try:
        # Cria diretório se não existir
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Verifica tamanho do arquivo (se disponível)
        if hasattr(file, 'size') and file.size:
            if file.size > max_size:
                raise HTTPException(
                    status_code=413,
                    detail=f"Arquivo muito grande. Tamanho máximo: {max_size / (1024*1024):.1f}MB"
                )
        
        # Salva arquivo em chunks com timeout
        with open(save_path, "wb") as buffer:
            while True:
                # Verifica timeout
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    # Remove arquivo parcial
                    if os.path.exists(save_path):
                        os.remove(save_path)
                    raise HTTPException(
                        status_code=408,
                        detail=f"Timeout no upload. Tempo máximo: {timeout}s"
                    )
                
                # Lê chunk
                try:
                    chunk = await asyncio.wait_for(
                        file.read(CHUNK_SIZE),
                        timeout=10.0  # Timeout por chunk
                    )
                except asyncio.TimeoutError:
                    if os.path.exists(save_path):
                        os.remove(save_path)
                    raise HTTPException(
                        status_code=408,
                        detail="Timeout ao ler dados do arquivo"
                    )
                
                if not chunk:
                    break
                
                # Verifica tamanho total
                bytes_read += len(chunk)
                if bytes_read > max_size:
                    if os.path.exists(save_path):
                        os.remove(save_path)
                    raise HTTPException(
                        status_code=413,
                        detail=f"Arquivo muito grande. Tamanho máximo: {max_size / (1024*1024):.1f}MB"
                    )
                
                # Escreve chunk
                buffer.write(chunk)
                
                # Callback de progresso
                if progress_callback:
                    progress_callback(bytes_read, file.size if hasattr(file, 'size') and file.size else None)
        
        file_size_mb = bytes_read / (1024 * 1024)
        duration_ms = (time.time() - start_time) * 1000
        
        app_logger.info(
            f"Upload salvo: {os.path.basename(save_path)} ({file_size_mb:.2f}MB) em {duration_ms:.2f}ms",
            extra={
                'filename': file.filename,
                'size_mb': round(file_size_mb, 2),
                'duration_ms': round(duration_ms, 2)
            }
        )
        
        return {
            'path': save_path,
            'size_bytes': bytes_read,
            'size_mb': round(file_size_mb, 2),
            'duration_ms': round(duration_ms, 2)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # Remove arquivo parcial em caso de erro
        if os.path.exists(save_path):
            try:
                os.remove(save_path)
            except:
                pass
        
        error_logger.error(f"Erro ao salvar upload: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Erro ao processar arquivo. Tente novamente."
        )


def validate_file_upload(file: UploadFile, allowed_extensions: list = None) -> dict:
    """
    Valida arquivo de upload antes de processar
    
    Args:
        file: Arquivo FastAPI UploadFile
        allowed_extensions: Lista de extensões permitidas (ex: ['.xlsx', '.xls'])
    
    Returns:
        Dict com informações de validação
    
    Raises:
        HTTPException: Se validação falhar
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nome de arquivo não fornecido")
    
    # Valida extensão
    if allowed_extensions:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Extensão não permitida. Permitidas: {', '.join(allowed_extensions)}"
            )
    
    # Valida content-type se disponível
    if hasattr(file, 'content_type') and file.content_type:
        allowed_types = [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel',
            'application/octet-stream'  # Para alguns navegadores
        ]
        if file.content_type not in allowed_types and not any(
            ct in file.content_type for ct in ['excel', 'spreadsheet']
        ):
            app_logger.warning(f"Content-type suspeito: {file.content_type} para arquivo {file.filename}")
    
    return {
        'filename': file.filename,
        'extension': os.path.splitext(file.filename)[1].lower(),
        'size': file.size if hasattr(file, 'size') and file.size else None
    }

