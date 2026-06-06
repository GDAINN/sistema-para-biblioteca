from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Optional
import secrets
import os 

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session

database_url = os.getenv("database_url")

engine = create_engine(database_url, connect_args= ({"check_same_thread": False}))
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
base = declarative_base()

app = FastAPI()
#criando um login para o minha api 
meu_usuario = os.getenv("meu_usuario")
meu_senha = os.getenv("meu_senha")

security = HTTPBasic()

meu_dicionario = {}

class LivroDB(base):
    __tablename__ = "Livros"
    id = Column(Integer, primary_key=True, index=True)
    nome_livro = Column(String, index=True)
    autor_livro = Column(String, index=True )
    ano_livro =Column(Integer)
    
class Livro(BaseModel):
    nome_livro: str
    autor_livro: str
    ano_livro: int

base.metadata.create_all(bind=engine)

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
    limit: int = 10,
    db: Session = Depends(sessao_db),
    credentials: HTTPBasicCredentials = Depends(autenticar_meu_usuario)
):
    livros = db.query(LivroDB).offset((page-1) * limit).all()
    
    # Validar paginação
    if page < 1 or limit < 1:
        raise HTTPException(status_code=400, detail="Page e limit devem ser maiores que 0.")

    if not livros:
        return {"message": "Nenhum livro encontrado."}

    total_livros= db.query(LivroDB).count()

    return {
        "page": page,
        "limit": limit,
        "total_livros": total_livros,
        "livros": [{"id": livro.id, "titulo": livro.nome_livro, "autor": livro.autor_livro, "ano": livro.ano_livro} for livro in livros]
    }
    

@app.post("/adicionar")
def post_livros(
    Livro: Livro,
    db: Session = Depends(sessao_db),
    credentials: HTTPBasicCredentials = Depends(autenticar_meu_usuario)
):
    
    db_livro = db.query(LivroDB).filter(
        LivroDB.nome_livro == Livro.nome_livro,
        LivroDB.autor_livro == Livro.autor_livro
    ).first()

    if db_livro:
        raise HTTPException(
            status_code=400,
            detail="Esse livro já existe dentro do banco de dados"
        )

    novo_livro = LivroDB(
        nome_livro=Livro.nome_livro,
        autor_livro=Livro.autor_livro,
        ano_livro=Livro.ano_livro
    )

    db.add(novo_livro)
    db.commit()
    db.refresh(novo_livro)

    return {"message": "Livro adicionado com sucesso."}


    
@app.put("/atualizar/{id}")
def put_livros(id: int, Livro: Livro, db: Session = Depends(sessao_db), credentials: HTTPBasicCredentials = Depends(autenticar_meu_usuario)):
    db_livro = db.query(LivroDB).filter(LivroDB.id == id).first()
    if not db_livro:
        raise HTTPException(status_code=404, detail="Livro não foi encontrado no banco de dados!.")
    db_livro.nome_livro = Livro.nome_livro
    db_livro.autor_livro = Livro.autor_livro
    db_livro.ano_livro = Livro.ano_livro

    db.commit()
    db.refresh(db_livro)

    return {"message": "Livro atualizado com sucesso."}


@app.delete("/deletar/{id}")
def delete_livros(id: int, db: Session = Depends(sessao_db), credentials: HTTPBasicCredentials = Depends(autenticar_meu_usuario)):
    db_livro = db.query(LivroDB).filter(LivroDB.id == id).first()

    if not db_livro:
        raise HTTPException(status_code=404, detail="Livro não encontrado no banco de dados!.")
    
    db.delete(db_livro)
    db.commit()

    return {"message": "Livro deletado com sucesso."}
