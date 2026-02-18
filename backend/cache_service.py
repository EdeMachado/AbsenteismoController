"""
Serviço de Cache Inteligente
Cache de dados frequentes com invalidação automática
"""
from typing import Any, Optional, Dict, Callable
from datetime import datetime, timedelta
import hashlib
import json

# Importa logger (com fallback)
try:
    from .logger import get_logger
    logger = get_logger("cache")
except ImportError:
    logger = None

class CacheService:
    """Serviço de cache com TTL"""
    
    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = 300  # 5 minutos padrão
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Gera chave de cache única"""
        key_data = {
            "prefix": prefix,
            "args": args,
            "kwargs": sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return f"{prefix}:{hashlib.md5(key_str.encode()).hexdigest()}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Obtém valor do cache
        
        Args:
            key: Chave do cache
            
        Returns:
            Valor ou None se não existir/expirado
        """
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        
        # Verifica expiração
        if datetime.now() > entry["expires_at"]:
            del self.cache[key]
            return None
        
        return entry["value"]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Define valor no cache
        
        Args:
            key: Chave do cache
            value: Valor a armazenar
            ttl: Time to live em segundos (None = default)
        """
        ttl = ttl or self.default_ttl
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        self.cache[key] = {
            "value": value,
            "expires_at": expires_at,
            "created_at": datetime.now().isoformat()
        }
    
    def get_or_set(
        self,
        key: str,
        func: Callable,
        ttl: Optional[int] = None,
        *args,
        **kwargs
    ) -> Any:
        """
        Obtém do cache ou executa função e armazena
        
        Args:
            key: Chave do cache
            func: Função a executar se não estiver em cache
            ttl: Time to live
            *args, **kwargs: Argumentos para a função
            
        Returns:
            Valor do cache ou resultado da função
        """
        # Tenta obter do cache
        cached = self.get(key)
        if cached is not None:
            return cached
        
        # Executa função
        value = func(*args, **kwargs)
        
        # Armazena no cache
        self.set(key, value, ttl)
        
        return value
    
    def invalidate(self, key: str):
        """Remove entrada do cache"""
        if key in self.cache:
            del self.cache[key]
    
    def invalidate_prefix(self, prefix: str):
        """Remove todas as entradas com prefixo"""
        keys_to_remove = [k for k in self.cache.keys() if k.startswith(prefix)]
        for key in keys_to_remove:
            del self.cache[key]
    
    def clear(self):
        """Limpa todo o cache"""
        self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        total = len(self.cache)
        expired = sum(
            1 for entry in self.cache.values()
            if datetime.now() > entry["expires_at"]
        )
        
        return {
            "total_entries": total,
            "active_entries": total - expired,
            "expired_entries": expired
        }

# Instância global
cache_service = CacheService()

# Helpers para cache comum
def cache_client(client_id: int, ttl: int = 3600):
    """Cache para dados de cliente (1 hora)"""
    return cache_service.get_or_set(
        f"client:{client_id}",
        lambda: None,  # Será substituído pela função real
        ttl=ttl
    )

def invalidate_client_cache(client_id: int):
    """Invalida cache de um cliente"""
    cache_service.invalidate_prefix(f"client:{client_id}")








