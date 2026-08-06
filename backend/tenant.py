"""
Guard central de tenant (S01-A).

Resolve o client_id autorizado a partir do usuário autenticado.
Não confia no valor enviado pelo frontend quando o usuário está vinculado a um cliente.
"""
from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from .models import Client, User


def resolve_authorized_client(
    db: Session,
    current_user: User,
    requested_client_id: Optional[int],
) -> Client:
    """
    Resolve e valida o cliente autorizado para a operação.

    Regras (S01-A):
    - Usuário com client_id definido: sempre usa o próprio; request diferente → 403.
    - Administrador explícito (is_admin=True): pode operar no client_id solicitado.
    - client_id NULL sem is_admin → 403 (não concede acesso global).
    - Cliente inexistente → 404.
    - Sem fallback silencioso para client_id=1.
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Usuário vinculado a um tenant: ignora/rejeita request divergente
    if current_user.client_id is not None:
        if requested_client_id is not None and int(requested_client_id) != int(current_user.client_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado: operação fora do cliente autorizado",
            )
        authorized_id = int(current_user.client_id)
    elif getattr(current_user, "is_admin", False):
        # Admin global explícito: exige client_id solicitado (sem default 1)
        if requested_client_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="client_id é obrigatório",
            )
        try:
            authorized_id = int(requested_client_id)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="client_id deve ser um número inteiro",
            )
        if authorized_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="client_id é obrigatório e deve ser maior que zero",
            )
    else:
        # Sem tenant e sem admin
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado: usuário sem cliente associado",
        )

    client = db.query(Client).filter(Client.id == authorized_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente com ID {authorized_id} não encontrado",
        )
    return client


def require_admin_user(current_user: User) -> User:
    """Exige administrador explícito (is_admin=True)."""
    if not current_user or not getattr(current_user, "is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Apenas administradores.",
        )
    return current_user
