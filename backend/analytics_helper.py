"""
Helper functions for applying filters in analytics queries
"""
from sqlalchemy import or_
from .models import Atestado

def aplicar_filtro_funcionario(query, funcionario):
    """Aplica filtro de funcionário (suporta string ou lista)"""
    if not funcionario:
        return query
    
    if isinstance(funcionario, list) and len(funcionario) > 0:
        # Múltiplos funcionários - usa OR
        conditions = []
        for func in funcionario:
            conditions.append(Atestado.nomecompleto == func)
            conditions.append(Atestado.nome_funcionario == func)
        return query.filter(or_(*conditions))
    elif isinstance(funcionario, str):
        # Único funcionário
        return query.filter(
            (Atestado.nomecompleto == funcionario) | (Atestado.nome_funcionario == funcionario)
        )
    
    return query

def aplicar_filtro_setor(query, setor):
    """Aplica filtro de setor (suporta string ou lista)"""
    if not setor:
        return query
    
    if isinstance(setor, list) and len(setor) > 0:
        # Múltiplos setores - usa OR
        return query.filter(Atestado.setor.in_(setor))
    elif isinstance(setor, str):
        # Único setor
        return query.filter(Atestado.setor == setor)
    
    return query

