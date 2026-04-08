from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Optional
import secrets
import os 

app = FastAPI()
#criando um login para o minha api 
meu_usuario = "admin"
meu_senha = "admin123"

security = HTTPBasic()

meu_dicionario = {}

class Livro(BaseModel):
    titulo: str
    autor: str
    ano: int


def autenticar_meu_usuario(credentials: HTTPBasicCredentials = Depends(security)):
    is_username_correct = secrets.compare_digest(credentials.username, meu_usuario)
    is_password_correct= secrets.compare_digest(credentials.password, meu_senha)
    if not (is_username_correct and is_password_correct):
        raise HTTPException(status_code=401, detail="Credenciais inválidas.", headers={"WWW-Authenticate": "Basic"})

@app.get("/livros")
def get_livros(credentials: HTTPBasicCredentials = Depends(autenticar_meu_usuario)):
    if not meu_dicionario:
        return {"message": "Nenhum livro encontrado."}
    else:
        return{"livros": meu_dicionario}

@app.post("/adicionar")
def post_livros(id: int, Livro: Livro, credentials: HTTPBasicCredentials = Depends(autenticar_meu_usuario)):
    if id in meu_dicionario:
        raise HTTPException(status_code=400,detail="Esse livro já existe.")
    else:
        meu_dicionario[id] = Livro.dict()
        return {"message": "Livro foi criado"}
    
@app.put("/atualizar/{id}")
def put_livros(id: int, Livro: Livro, credentials: HTTPBasicCredentials = Depends(autenticar_meu_usuario)):
    meu_livros = meu_dicionario.get(id)
    if not meu_livros:
        raise HTTPException(status_code=404, detail="Livro não encontrado.")
    else:
      meu_dicionario[id] = Livro.dict()
        
    return {"message": "Livro atualizado com sucesso."}

@app.delete("/deletar/{id}")
def delete_livros(id: int):
    if id not in meu_dicionario:
        raise HTTPException(status_code=404, detail="Livro não encontrado.")
    else:
        del meu_dicionario[id]
        return {"message": "Livro deletado com sucesso."}
