from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
import secrets
import os
import redis
import json

from task import fatorial, somar
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# =========================
# Banco de Dados
# =========================

database_url = os.getenv("database_url")

engine = create_engine(
    database_url,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# =========================
# Redis
# =========================
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=0,
    decode_responses=True
)

# =========================
# FastAPI
# =========================

app = FastAPI()

# =========================
# Autenticação
# =========================

meu_usuario = os.getenv("meu_usuario")
meu_senha = os.getenv("meu_senha")

security = HTTPBasic()

# =========================
# Modelos
# =========================

class LivroDB(Base):
    __tablename__ = "Livros"

    id = Column(Integer, primary_key=True, index=True)
    nome_livro = Column(String, index=True)
    autor_livro = Column(String, index=True)
    ano_livro = Column(Integer)


class Livro(BaseModel):
    nome_livro: str
    autor_livro: str
    ano_livro: int

# =========================
# Criar tabelas
# =========================

Base.metadata.create_all(bind=engine)

# =========================
# Sessão do banco
# =========================

def sessao_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =========================
# Redis
# =========================

def salvar_livro_redis(livro_id: int, livro: Livro):
    redis_client.set(
        f"Livro:{livro_id}",
        json.dumps(livro.model_dump())
    )


def deletar_livro_redis(livro_id: int):
    redis_client.delete(f"Livro:{livro_id}")

# =========================
# Login
# =========================

def autenticar_meu_usuario(
    credentials: HTTPBasicCredentials = Depends(security)
):
    usuario_ok = secrets.compare_digest(
        credentials.username,
        meu_usuario
    )

    senha_ok = secrets.compare_digest(
        credentials.password,
        meu_senha
    )

    if not (usuario_ok and senha_ok):
        raise HTTPException(
            status_code=401,
            detail="Credenciais inválidas.",
            headers={"WWW-Authenticate": "Basic"},
        )

# =========================
# Celery
# =========================

@app.post("/calcular/somar")
def calcular_soma(a: int, b: int):

    tarefa = somar.delay(a, b)

    return {
        "task_id": tarefa.id,
        "mensagem": "Tarefa de soma enviada para execução."
    }


@app.post("/calcular/fatorial")
def calcular_fatorial(n: int):

    tarefa = fatorial.delay(n)

    return {
        "task_id": tarefa.id,
        "mensagem": "Tarefa de fatorial enviada para execução."
    }

# =========================
# Livros
# =========================

@app.get("/livros")
def get_livros(
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(sessao_db),
    credentials: HTTPBasicCredentials = Depends(autenticar_meu_usuario)
):

    if page < 1 or limit < 1:
        raise HTTPException(
            status_code=400,
            detail="Page e limit devem ser maiores que zero."
        )

    livros = db.query(LivroDB)\
        .offset((page - 1) * limit)\
        .limit(limit)\
        .all()

    total = db.query(LivroDB).count()

    return {
        "page": page,
        "limit": limit,
        "total_livros": total,
        "livros": livros
    }


@app.post("/adicionar")
def post_livros(
    livro: Livro,
    db: Session = Depends(sessao_db),
    credentials: HTTPBasicCredentials = Depends(autenticar_meu_usuario)
):

    existe = db.query(LivroDB).filter(
        LivroDB.nome_livro == livro.nome_livro,
        LivroDB.autor_livro == livro.autor_livro
    ).first()

    if existe:
        raise HTTPException(
            status_code=400,
            detail="Livro já cadastrado."
        )

    novo = LivroDB(
        nome_livro=livro.nome_livro,
        autor_livro=livro.autor_livro,
        ano_livro=livro.ano_livro
    )

    db.add(novo)
    db.commit()
    db.refresh(novo)

    salvar_livro_redis(novo.id, livro)

    return {
        "message": "Livro adicionado com sucesso."
    }


@app.put("/atualizar/{id}")
def atualizar_livro(
    id: int,
    livro: Livro,
    db: Session = Depends(sessao_db),
    credentials: HTTPBasicCredentials = Depends(autenticar_meu_usuario)
):

    db_livro = db.query(LivroDB).filter(
        LivroDB.id == id
    ).first()

    if not db_livro:
        raise HTTPException(
            status_code=404,
            detail="Livro não encontrado."
        )

    db_livro.nome_livro = livro.nome_livro
    db_livro.autor_livro = livro.autor_livro
    db_livro.ano_livro = livro.ano_livro

    db.commit()
    db.refresh(db_livro)

    salvar_livro_redis(id, livro)

    return {
        "message": "Livro atualizado com sucesso."
    }


@app.delete("/deletar/{id}")
def deletar_livro(
    id: int,
    db: Session = Depends(sessao_db),
    credentials: HTTPBasicCredentials = Depends(autenticar_meu_usuario)
):

    db_livro = db.query(LivroDB).filter(
        LivroDB.id == id
    ).first()

    if not db_livro:
        raise HTTPException(
            status_code=404,
            detail="Livro não encontrado."
        )

    db.delete(db_livro)
    db.commit()

    deletar_livro_redis(id)

    return {
        "message": "Livro deletado com sucesso."
    }