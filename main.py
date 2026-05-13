from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Optional
import secrets
import os 

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

database_url = "sqlite:///./livros.db"

engime = create_engine(database_url, connect_args= ({"check_same_thread": False}))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engime)
base = declarative_base()

app = FastAPI()
#criando um login para o minha api 
meu_usuario = "admin"
meu_senha = "admin123"

security = HTTPBasic()

meu_dicionario = {}

class LivroDB(base):
    __tablename__ = "Livros"
    id = Column(Integer, primary_key=True, index=True)
    nome_livro = Column(String, index=True)
    autor_livro = Column(String, index=True )
    ano_livro =Column(Integer)
    
class Livro(BaseModel):
    titulo: str
    autor: str
    ano: int

base.metadata.create_all(bind=engime)

def sessao_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Função para autenticar o usuário usando HTTP Basic Authentication
def autenticar_meu_usuario(credentials: HTTPBasicCredentials = Depends(security)):
    is_username_correct = secrets.compare_digest(credentials.username, meu_usuario)
    is_password_correct= secrets.compare_digest(credentials.password, meu_senha)
    if not (is_username_correct and is_password_correct):
        raise HTTPException(status_code=401, detail="Credenciais inválidas.", headers={"WWW-Authenticate": "Basic"})

@app.get("/livros")
def get_livros(
    page: int = 1,
    limit: int = 10, db: SessionLocal = Depends(sessao_db),
    credentials: HTTPBasicCredentials = Depends(autenticar_meu_usuario)
):
    livros = db.query(LivroDB).offset(page-1).limit(limit).all()

    # Validar paginação
    if page < 1 or limit < 1:
        raise HTTPException(status_code=400, detail="Page e limit devem ser maiores que 0.")

    if not meu_dicionario:
        return {"message": "Nenhum livro encontrado."}

    total_livros= db.query(LivroDB).count()

    return {
        "page": page,
        "limit": limit,
        "total_livros": total_livros,
        "livros": [{"id": livro.id, "titulo": livro.nome_livro, "autor": livro.autor_livro, "ano": livro.ano_livro} for livro in livros]
    }
    

@app.post("/adicionar")
def post_livros(Livro: Livro, db: SessionLocal = Depends(sessao_db), credentials: HTTPBasicCredentials = Depends(autenticar_meu_usuario)):
    db_livro = db.query(LivroDB).filter(LivroDB.nome_livro == Livro.nome_livro, LivroDB.autor_livro == Livro.autor_livro).first()
    if db_livro:
        raise HTTPException(status_code=400, detail="Esse livros já existe dentro do banco de dados")
    novo_livro = LivroDB(nome_livro=Livro.nome_livro, autor_livro=Livro.
    autor_livro, ano_livro=Livro.ano_livro)

    db.add(novo_livro)
    db.commit()
    db.refresh(novo_livro)

    return {"message": "Livro adicionado com sucesso."}


    
@app.put("/atualizar/{id}")
def put_livros(id: int, Livro: Livro, db: SessionLocal = Depends(sessao_db), credentials: HTTPBasicCredentials = Depends(autenticar_meu_usuario)):
    db_livro = db.query(LivroDB).filter(LivroDB.id == id).first()
    if not db_livro:
        raise HTTPException(status_code=404, detail="Livro não encontrado.")
    else:
        for key, value in Livro.dict().items():
            setattr(db_livro, key, value)
        db.commit()
        db.refresh(db_livro)
    return {"message": "Livro atualizado com sucesso."}

@app.delete("/deletar/{id}")
def delete_livros(id: int):
    if id not in meu_dicionario:
        raise HTTPException(status_code=404, detail="Livro não encontrado.")
    else:
        del meu_dicionario[id]
        return {"message": "Livro deletado com sucesso."}
