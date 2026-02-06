"""
Processador Assíncrono para Operações Longas
Permite processamento em background com timeout e cancelamento
"""
import asyncio
from typing import Optional, Callable, Any, Dict
from datetime import datetime
import uuid

# Importa logger (com fallback)
try:
    from .logger import get_logger
    logger = get_logger("async")
except ImportError:
    logger = None

class AsyncTaskManager:
    """Gerenciador de tarefas assíncronas"""
    
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
    
    async def run_with_timeout(
        self,
        task_id: str,
        coro: Callable,
        timeout: int = 300,  # 5 minutos padrão
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Executa tarefa assíncrona com timeout
        
        Args:
            task_id: ID único da tarefa
            coro: Corrotina a executar
            timeout: Timeout em segundos
            *args, **kwargs: Argumentos para a corrotina
            
        Returns:
            Resultado da tarefa ou erro de timeout
        """
        try:
            # Registra tarefa
            self.tasks[task_id] = {
                "status": "running",
                "started_at": datetime.now().isoformat(),
                "timeout": timeout
            }
            
            # Executa com timeout
            result = await asyncio.wait_for(
                coro(*args, **kwargs),
                timeout=timeout
            )
            
            # Atualiza status
            self.tasks[task_id].update({
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "result": result
            })
            
            return {
                "success": True,
                "task_id": task_id,
                "result": result
            }
            
        except asyncio.TimeoutError:
            # Timeout
            self.tasks[task_id].update({
                "status": "timeout",
                "error": f"Tarefa excedeu timeout de {timeout}s"
            })
            
            if logger:
                logger.warning(f"Tarefa {task_id} excedeu timeout")
            
            return {
                "success": False,
                "task_id": task_id,
                "error": "Timeout - operação demorou muito"
            }
            
        except Exception as e:
            # Erro
            self.tasks[task_id].update({
                "status": "error",
                "error": str(e),
                "completed_at": datetime.now().isoformat()
            })
            
            if logger:
                logger.error(f"Erro na tarefa {task_id}: {e}")
            
            return {
                "success": False,
                "task_id": task_id,
                "error": str(e)
            }
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retorna status de uma tarefa"""
        return self.tasks.get(task_id)
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancela uma tarefa (se ainda estiver rodando)"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            if task["status"] == "running":
                task["status"] = "cancelled"
                task["cancelled_at"] = datetime.now().isoformat()
                return True
        return False

# Instância global
task_manager = AsyncTaskManager()

