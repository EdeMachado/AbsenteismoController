"""
Sistema de autenticação
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import bcrypt
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional
from .database import get_db
from .models import User, Config
import secrets

# Configuração de segurança
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"  # Em produção, usar variável de ambiente
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 horas

# Security scheme
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha está correta"""
    try:
        # Converte para bytes se necessário
        if isinstance(plain_password, str):
            plain_password = plain_password.encode('utf-8')
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode('utf-8')
        return bcrypt.checkpw(plain_password, hashed_password)
    except Exception as e:
        print(f"Erro ao verificar senha: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Gera hash da senha"""
    # Converte para bytes se necessário
    if isinstance(password, str):
        password = password.encode('utf-8')
    # Gera salt e hash
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password, salt)
    # Retorna como string
    return hashed.decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Cria token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_user(db: Session, username: str, password: str):
    """Autentica usuário"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not user.is_active:
        return False
    if not verify_password(password, user.password_hash):
        return False
    # Atualiza último login
    user.last_login = datetime.now()
    db.commit()
    return user

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Obtém usuário atual a partir do token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não autenticado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Usuário inativo")
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Obtém usuário ativo atual"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Usuário inativo")
    return current_user

def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Obtém usuário admin atual"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Acesso negado. Apenas administradores.")
    return current_user

def get_config_value(db: Session, chave: str, default: any = None) -> any:
    """Obtém valor de configuração"""
    config = db.query(Config).filter(Config.chave == chave).first()
    if not config:
        return default
    if config.tipo == "boolean":
        return config.valor.lower() in ("true", "1", "yes", "sim")
    elif config.tipo == "number":
        try:
            return float(config.valor) if "." in config.valor else int(config.valor)
        except:
            return default
    elif config.tipo == "json":
        import json
        try:
            return json.loads(config.valor)
        except:
            return default
    return config.valor

def set_config_value(db: Session, chave: str, valor: any, descricao: str = None, tipo: str = "string"):
    """Define valor de configuração"""
    config = db.query(Config).filter(Config.chave == chave).first()
    if config:
        if tipo == "json":
            import json
            config.valor = json.dumps(valor)
        else:
            config.valor = str(valor)
        config.tipo = tipo
        if descricao:
            config.descricao = descricao
        config.updated_at = datetime.now()
    else:
        if tipo == "json":
            import json
            valor_str = json.dumps(valor)
        else:
            valor_str = str(valor)
        config = Config(
            chave=chave,
            valor=valor_str,
            descricao=descricao,
            tipo=tipo
        )
        db.add(config)
    db.commit()
    return config

