from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
app = FastAPI()

meu_dicionario = {}

class Livro(BaseModel):
    titulo: str
    autor: str
    ano: int

@app.get("/livros")
def get_livros():
    if not meu_dicionario:
        return {"message": "Nenhum livro encontrado."}
    else:
        return{"livros": meu_dicionario}

@app.post("/adicionar")
def post_livros(id: int, Livro: Livro):
    if id in meu_dicionario:
        raise HTTPException(status_code=400,detail="Esse livro já existe.")
    else:
        meu_dicionario[id] = Livro.dict()
        return {"message": "Livro foi criado"}
    
@app.put("/atualizar/{id}")
def put_livros(id: int, Livro: Livro):
    meu_livros = meu_dicionario.get(id)
    if not meu_livros:
        raise HTTPException(status_code=404, detail="Livro não encontrado.")
    else:
        meu_livros[id] = Livro.dict()
        
        return {"message": "Livro atualizado com sucesso."}

@app.delete("/deletar/{id}")
def delete_livros(id: int):
    if id not in meu_dicionario:
        raise HTTPException(status_code=404, detail="Livro não encontrado.")
    else:
        del meu_dicionario[id]
        return {"message": "Livro deletado com sucesso."}
