"""
Middleware de Logging de Requisições
Registra todas as requisições HTTP para auditoria e monitoramento
"""
import time
from fastapi import Request
from .logger import app_logger, security_logger
from typing import Callable


async def request_logging_middleware(request: Request, call_next: Callable):
    """
    Middleware que registra todas as requisições HTTP
    
    Registra:
    - Método HTTP
    - URL
    - IP do cliente
    - Tempo de resposta
    - Status code
    - Tamanho da resposta
    """
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"
    
    # Ignora requisições para arquivos estáticos em produção
    if request.url.path.startswith("/static/"):
        response = await call_next(request)
        return response
    
    # Log da requisição
    app_logger.info(
        f"{request.method} {request.url.path}",
        extra={
            'method': request.method,
            'path': request.url.path,
            'query_params': str(request.query_params),
            'client_ip': client_ip,
            'user_agent': request.headers.get('user-agent', 'unknown')
        }
    )
    
    # Processa requisição
    try:
        response = await call_next(request)
        
        # Calcula tempo de resposta
        duration_ms = (time.time() - start_time) * 1000
        
        # Log de resposta
        status_code = response.status_code
        
        # Log de segurança para códigos de erro
        if status_code >= 400:
            if status_code == 401:
                security_logger.warning(
                    "Acesso não autorizado",
                    extra={
                        'method': request.method,
                        'path': request.url.path,
                        'client_ip': client_ip,
                        'status_code': status_code
                    }
                )
            elif status_code == 403:
                security_logger.warning(
                    "Acesso negado",
                    extra={
                        'method': request.method,
                        'path': request.url.path,
                        'client_ip': client_ip,
                        'status_code': status_code
                    }
                )
            elif status_code >= 500:
                app_logger.error(
                    f"Erro interno: {status_code}",
                    extra={
                        'method': request.method,
                        'path': request.url.path,
                        'client_ip': client_ip,
                        'status_code': status_code,
                        'duration_ms': duration_ms
                    }
                )
        
        # Adiciona header com tempo de resposta
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        
        # Log de performance para requisições lentas
        if duration_ms > 5000:  # Mais de 5 segundos
            app_logger.warning(
                f"Requisição lenta: {duration_ms:.2f}ms",
                extra={
                    'method': request.method,
                    'path': request.url.path,
                    'duration_ms': duration_ms,
                    'status_code': status_code
                }
            )
        
        return response
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        app_logger.error(
            f"Erro ao processar requisição: {str(e)}",
            exc_info=True,
            extra={
                'method': request.method,
                'path': request.url.path,
                'client_ip': client_ip,
                'duration_ms': duration_ms
            }
        )
        raise

